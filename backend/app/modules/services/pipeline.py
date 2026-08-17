import re
import traceback
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import get_settings
from app.models import AuditLog, Chunk, Document, ExtractionRun, Link, LinkType, Object, ObjectType
from app.schemas import ProcessResult
from app.modules.services import parsing
from app.modules.services.llm import LLM

_SAMPLE_CHUNKS = 8
_MAX_CHUNKS_PER_DOC = 60


def run_pipeline(document_id: str, raw_bytes: bytes | None = None) -> ProcessResult:
    from app.db import SessionLocal

    with SessionLocal() as db:
        doc = db.get(Document, document_id)
        if doc is None:
            return ProcessResult(document_id=document_id, status="failed", error="document not found")
        try:
            if raw_bytes is not None and not doc.raw_text:
                doc.raw_text = parsing.extract_text(doc.filename, raw_bytes)
            return _process(db, doc)
        except Exception as e:  # noqa: BLE001 - 后台任务需把任何失败落库供排查
            db.rollback()
            doc.status, doc.error = "failed", f"{e}\n{traceback.format_exc()[-1000:]}"
            db.commit()
            return ProcessResult(document_id=document_id, status="failed", error=str(e))


def _process(db: Session, doc: Document) -> ProcessResult:
    settings = get_settings()
    llm = LLM()
    doc.status = "parsed"
    db.commit()

    db.query(Chunk).filter(Chunk.document_id == doc.id).delete()
    chunks_text = parsing.chunk_text(doc.raw_text)[:_MAX_CHUNKS_PER_DOC]
    chunks = [Chunk(document_id=doc.id, seq=i, text=t) for i, t in enumerate(chunks_text)]
    db.add_all(chunks)
    db.commit()

    induction_run = ExtractionRun(document_id=doc.id, stage="induction", model=llm.model_label)
    db.add(induction_run)
    db.commit()
    # induction 失败时降级：若库里已有归纳过的本体，直接复用进抽取，不整文档 failed
    try:
        proposal = llm.induce_schema(chunks_text[:_SAMPLE_CHUNKS])
        new_types = _merge_proposed_schema(db, proposal, doc.id)
        induction_run.status, induction_run.finished_at = "ok", datetime.now(timezone.utc)
        induction_run.summary = {
            "proposed_object_types": len(proposal.get("object_types", [])),
            "proposed_link_types": len(proposal.get("link_types", [])),
            "created_object_types": new_types["object_types"],
            "created_link_types": new_types["link_types"],
        }
    except Exception as e:  # noqa: BLE001 - 归纳失败但已有本体时降级复用
        existing_types = db.scalars(select(ObjectType).where(ObjectType.status != "archived")).all()
        if not existing_types:
            # 无可复用本体：induction 硬失败，落 ExtractionRun=failed 再抛，由 run_pipeline 兜底转 document failed（层 4 错误路径）
            induction_run.status, induction_run.finished_at = "failed", datetime.now(timezone.utc)
            induction_run.summary = {"error": f"{type(e).__name__}: {e}"[:200]}
            db.commit()
            raise
        new_types = {"object_types": 0, "link_types": 0}
        induction_run.status, induction_run.finished_at = "failed", datetime.now(timezone.utc)
        induction_run.summary = {"degraded": True, "error": f"{type(e).__name__}: {e}"[:200], "reused_object_types": len(existing_types)}
    db.commit()

    objects_upserted, links_upserted = 0, 0
    extraction_run = ExtractionRun(document_id=doc.id, stage="extraction", model=llm.model_label)
    db.add(extraction_run)
    db.commit()
    failed_chunks: list[dict] = []
    for chunk in chunks:
        digest = _schema_digest(db)
        try:
            result = llm.extract_instances(chunk.text, digest)
        except Exception as e:  # noqa: BLE001 - 单块 LLM 调用失败不应整文档 failed；记录后继续下一块
            failed_chunks.append({"chunk_seq": chunk.seq, "error": f"{type(e).__name__}: {e}"[:200]})
            continue
        objects_upserted += _upsert_objects(db, result.get("objects", []), chunk.id)
        links_upserted += _upsert_links(db, result.get("links", []), chunk.id)
    extraction_run.status = "ok" if not failed_chunks else "partial"
    extraction_run.finished_at = datetime.now(timezone.utc)
    extraction_run.summary = {
        "objects_upserted": objects_upserted,
        "links_upserted": links_upserted,
        "failed_chunks": failed_chunks,
    }

    doc.status = "processed"
    db.add(AuditLog(action="process", entity="document", entity_id=doc.id, detail={"chunks": len(chunks)}))
    db.commit()
    return ProcessResult(
        document_id=doc.id,
        status="processed",
        chunks=len(chunks),
        new_object_types=new_types.get("object_types", 0) if isinstance(new_types, dict) else 0,
        objects_upserted=objects_upserted,
        links_upserted=links_upserted,
    )


def _merge_proposed_schema(db: Session, proposal: dict, document_id: str) -> dict:
    created = {"object_types": 0, "link_types": 0}
    for t in proposal.get("object_types", []):
        name = _slug(t.get("name", ""))
        if not name or db.scalar(select(ObjectType).where(ObjectType.name == name)):
            continue
        db.add(
            ObjectType(
                name=name,
                display_name=t.get("display_name") or name,
                description=t.get("description", ""),
                properties=[
                    {
                        "name": _slug(p.get("name", "")),
                        "display_name": p.get("display_name", ""),
                        "dtype": p.get("dtype", "string"),
                        "description": p.get("description", ""),
                    }
                    for p in t.get("properties", [])
                    if _slug(p.get("name", ""))
                ],
                status="draft",
                provenance="llm",
                source_document_id=document_id,
            )
        )
        created["object_types"] += 1
    db.flush()

    for lt in proposal.get("link_types", []):
        name = _slug(lt.get("name", ""))
        if not name or db.scalar(select(LinkType).where(LinkType.name == name)):
            continue
        src = db.scalar(select(ObjectType).where(ObjectType.name == _slug(lt.get("source", ""))))
        tgt = db.scalar(select(ObjectType).where(ObjectType.name == _slug(lt.get("target", ""))))
        if not src or not tgt:
            continue
        db.add(
            LinkType(
                name=name,
                display_name=lt.get("display_name") or name,
                description=lt.get("description", ""),
                source_object_type_id=src.id,
                target_object_type_id=tgt.id,
                cardinality=lt.get("cardinality", "many_to_many"),
                status="draft",
                provenance="llm",
            )
        )
        created["link_types"] += 1
    db.commit()
    return created


def _schema_digest(db: Session) -> str:
    types = db.scalars(select(ObjectType).where(ObjectType.status != "archived")).all()
    links = db.scalars(select(LinkType).where(LinkType.status != "archived")).all()
    by_id = {t.id: t.name for t in types}
    lines = ["object_types:"]
    for t in types:
        props = ", ".join(p["name"] for p in t.properties)
        lines.append(f"- {t.name}({props}): {t.description[:120]}")
    lines.append("link_types:")
    for lt in links:
        lines.append(f"- {lt.name}: {by_id.get(lt.source_object_type_id)} -> {by_id.get(lt.target_object_type_id)}")
    return "\n".join(lines)


def _upsert_objects(db: Session, items: list[dict], chunk_id: str) -> int:
    count = 0
    for item in items:
        type_name = _slug(item.get("type", ""))
        title = str(item.get("title", "")).strip()
        if not type_name or not title:
            continue
        obj_type = db.scalar(select(ObjectType).where(ObjectType.name == type_name))
        if obj_type is None:
            continue
        key = _title_key(title)
        existing = db.scalar(
            select(Object).where(Object.object_type_id == obj_type.id, Object.title_key == key)
        )
        props = {str(k): v for k, v in (item.get("properties") or {}).items() if v not in (None, "")}
        conf = max(0.0, min(1.0, float(item.get("confidence", 0.5))))
        if existing:
            merged = {**existing.properties, **props}
            existing.properties = merged
            existing.confidence = max(existing.confidence, conf)
            if chunk_id not in existing.source_chunk_ids:
                existing.source_chunk_ids = [*existing.source_chunk_ids, chunk_id]
        else:
            db.add(
                Object(
                    object_type_id=obj_type.id,
                    title=title,
                    title_key=key,
                    properties=props,
                    confidence=conf,
                    source_chunk_ids=[chunk_id],
                )
            )
        count += 1
    db.commit()
    return count


def _upsert_links(db: Session, items: list[dict], chunk_id: str) -> int:
    count = 0
    for item in items:
        link_name = _slug(item.get("link_type", ""))
        src_title, tgt_title = _title_key(item.get("source_title", "")), _title_key(item.get("target_title", ""))
        if not link_name or not src_title or not tgt_title:
            continue
        link_type = db.scalar(select(LinkType).where(LinkType.name == link_name))
        if link_type is None:
            continue
        src = db.scalar(select(Object).where(Object.object_type_id == link_type.source_object_type_id, Object.title_key == src_title))
        tgt = db.scalar(select(Object).where(Object.object_type_id == link_type.target_object_type_id, Object.title_key == tgt_title))
        if src is None or tgt is None:
            continue
        existing = db.scalar(
            select(Link).where(
                Link.link_type_id == link_type.id,
                Link.source_object_id == src.id,
                Link.target_object_id == tgt.id,
            )
        )
        conf = max(0.0, min(1.0, float(item.get("confidence", 0.5))))
        if existing:
            existing.confidence = max(existing.confidence, conf)
        else:
            db.add(Link(link_type_id=link_type.id, source_object_id=src.id, target_object_id=tgt.id, confidence=conf, source_chunk_id=chunk_id))
        count += 1
    db.commit()
    return count


def _slug(name: str) -> str:
    return re.sub(r"[^a-z0-9_]", "", str(name).strip().lower().replace("-", "_"))


def _title_key(title: str) -> str:
    return re.sub(r"\s+", " ", str(title).strip().lower())
