import uuid
from datetime import datetime, timezone

from sqlalchemy import Float, ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _uuid() -> str:
    return uuid.uuid4().hex


# provenance 取值：llm（模型生成草稿）/ llm_approved（模型生成+人工审核）/ human（人工创建）
# status 取值：draft / approved / archived
class Document(Base):
    __tablename__ = "documents"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    filename: Mapped[str] = mapped_column(Text)
    mime_type: Mapped[str] = mapped_column(String(120), default="")
    raw_text: Mapped[str] = mapped_column(Text, default="")
    status: Mapped[str] = mapped_column(String(20), default="uploaded")  # uploaded/parsed/processed/failed
    error: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(default=_now)


class Chunk(Base):
    __tablename__ = "chunks"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    document_id: Mapped[str] = mapped_column(ForeignKey("documents.id", ondelete="CASCADE"), index=True)
    seq: Mapped[int]
    text: Mapped[str] = mapped_column(Text)


class ObjectType(Base):
    __tablename__ = "object_types"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    name: Mapped[str] = mapped_column(String(80), unique=True)  # snake_case 标识
    display_name: Mapped[str] = mapped_column(Text)
    description: Mapped[str] = mapped_column(Text, default="")
    # [{name, display_name, dtype, description}]，Palantir 式动态属性 schema
    properties: Mapped[list] = mapped_column(JSONB, default=list)
    status: Mapped[str] = mapped_column(String(20), default="draft")
    provenance: Mapped[str] = mapped_column(String(20), default="llm")
    source_document_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    created_at: Mapped[datetime] = mapped_column(default=_now)
    updated_at: Mapped[datetime] = mapped_column(default=_now, onupdate=_now)


class LinkType(Base):
    __tablename__ = "link_types"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    name: Mapped[str] = mapped_column(String(80), unique=True)
    display_name: Mapped[str] = mapped_column(Text)
    description: Mapped[str] = mapped_column(Text, default="")
    source_object_type_id: Mapped[str] = mapped_column(ForeignKey("object_types.id"))
    target_object_type_id: Mapped[str] = mapped_column(ForeignKey("object_types.id"))
    cardinality: Mapped[str] = mapped_column(String(20), default="many_to_many")
    status: Mapped[str] = mapped_column(String(20), default="draft")
    provenance: Mapped[str] = mapped_column(String(20), default="llm")
    created_at: Mapped[datetime] = mapped_column(default=_now)


class Object(Base):
    __tablename__ = "objects"
    __table_args__ = (UniqueConstraint("object_type_id", "title_key", name="uq_object_identity"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    object_type_id: Mapped[str] = mapped_column(ForeignKey("object_types.id"), index=True)
    title: Mapped[str] = mapped_column(Text)
    title_key: Mapped[str] = mapped_column(Text)  # 归一化去重键
    properties: Mapped[dict] = mapped_column(JSONB, default=dict)
    status: Mapped[str] = mapped_column(String(20), default="draft")
    provenance: Mapped[str] = mapped_column(String(20), default="llm")
    confidence: Mapped[float] = mapped_column(Float, default=0.0)
    source_chunk_ids: Mapped[list] = mapped_column(JSONB, default=list)
    created_at: Mapped[datetime] = mapped_column(default=_now)
    updated_at: Mapped[datetime] = mapped_column(default=_now, onupdate=_now)


class Link(Base):
    __tablename__ = "links"
    __table_args__ = (UniqueConstraint("link_type_id", "source_object_id", "target_object_id", name="uq_link_identity"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    link_type_id: Mapped[str] = mapped_column(ForeignKey("link_types.id"), index=True)
    source_object_id: Mapped[str] = mapped_column(ForeignKey("objects.id"), index=True)
    target_object_id: Mapped[str] = mapped_column(ForeignKey("objects.id"), index=True)
    status: Mapped[str] = mapped_column(String(20), default="draft")  # draft/approved/archived
    provenance: Mapped[str] = mapped_column(String(20), default="llm")
    confidence: Mapped[float] = mapped_column(Float, default=0.0)
    source_chunk_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    created_at: Mapped[datetime] = mapped_column(default=_now)


class ExtractionRun(Base):
    __tablename__ = "extraction_runs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    document_id: Mapped[str] = mapped_column(ForeignKey("documents.id", ondelete="CASCADE"), index=True)
    stage: Mapped[str] = mapped_column(String(20))  # induction / extraction
    model: Mapped[str] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(20), default="running")  # running/ok/failed
    summary: Mapped[dict] = mapped_column(JSONB, default=dict)
    error: Mapped[str] = mapped_column(Text, default="")
    started_at: Mapped[datetime] = mapped_column(default=_now)
    finished_at: Mapped[datetime | None] = mapped_column(nullable=True)


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    actor: Mapped[str] = mapped_column(Text, default="anonymous")
    action: Mapped[str] = mapped_column(Text)  # approve/reject/create/update/delete
    entity: Mapped[str] = mapped_column(Text)  # object_type/link_type/object/link
    entity_id: Mapped[str] = mapped_column(String(36))
    detail: Mapped[dict] = mapped_column(JSONB, default=dict)
    created_at: Mapped[datetime] = mapped_column(default=_now)
