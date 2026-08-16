from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session, aliased

from app.db import get_db
from app.models import AuditLog, Link, LinkType, Object, ObjectType
from app.schemas import LinkOut, ReviewAction

router = APIRouter()

_ENTITIES = {"object_type": ObjectType, "link_type": LinkType, "object": Object, "link": Link}


@router.get("/queue")
def review_queue(db: Session = Depends(get_db)):
    source_obj = aliased(Object)
    target_obj = aliased(Object)
    link_rows = db.execute(
        select(Link, LinkType, source_obj, target_obj)
        .join(LinkType, Link.link_type_id == LinkType.id)
        .join(source_obj, Link.source_object_id == source_obj.id, isouter=True)
        .join(target_obj, Link.target_object_id == target_obj.id, isouter=True)
        .where(Link.status == "draft")
        .order_by(Link.confidence.desc())
        .limit(50)
    ).all()
    links = [
        LinkOut(
            id=link.id,
            link_type_id=link.link_type_id,
            link_type_name=link_type.name,
            source_object_id=link.source_object_id,
            source_title=src.title if src else "",
            target_object_id=link.target_object_id,
            target_title=tgt.title if tgt else "",
            status=link.status,
            provenance=link.provenance,
            confidence=link.confidence,
        )
        for link, link_type, src, tgt in link_rows
    ]
    return {
        "object_types": db.scalars(select(ObjectType).where(ObjectType.status == "draft").limit(50)).all(),
        "link_types": db.scalars(select(LinkType).where(LinkType.status == "draft").limit(50)).all(),
        "objects": db.scalars(select(Object).where(Object.status == "draft").order_by(Object.confidence.desc()).limit(50)).all(),
        "links": links,
    }


@router.post("/{entity}/{entity_id}/approve")
def approve(entity: str, entity_id: str, payload: ReviewAction, db: Session = Depends(get_db)):
    row = _load(db, entity, entity_id)
    row.status = "approved"
    if row.provenance == "llm":
        row.provenance = "llm_approved"
    db.add(
        AuditLog(
            actor=payload.actor,
            action="approve",
            entity=entity,
            entity_id=entity_id,
            detail={"comment": payload.comment},
        )
    )
    db.commit()
    return {"id": entity_id, "status": row.status, "provenance": row.provenance}


@router.post("/{entity}/{entity_id}/reject")
def reject(entity: str, entity_id: str, payload: ReviewAction, db: Session = Depends(get_db)):
    row = _load(db, entity, entity_id)
    row.status = "archived"
    db.add(
        AuditLog(
            actor=payload.actor,
            action="reject",
            entity=entity,
            entity_id=entity_id,
            detail={"comment": payload.comment},
        )
    )
    db.commit()
    return {"id": entity_id, "status": row.status}


def _load(db: Session, entity: str, entity_id: str):
    model = _ENTITIES.get(entity)
    if model is None:
        raise HTTPException(400, f"未知实体类型：{entity}，可选：{sorted(_ENTITIES)}")
    row = db.get(model, entity_id)
    if row is None:
        raise HTTPException(404, f"{entity} not found")
    return row
