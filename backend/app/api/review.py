from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import get_db
from app.models import AuditLog, Link, LinkType, Object, ObjectType
from app.schemas import ObjectTypeOut, ObjectOut, LinkTypeOut, ReviewAction

router = APIRouter(prefix="/review")

_ENTITIES = {"object_type": ObjectType, "link_type": LinkType, "object": Object, "link": Link}


@router.get("/queue")
def review_queue(db: Session = Depends(get_db)):
    return {
        "object_types": ObjectTypeOut.model_validate(
            db.scalars(select(ObjectType).where(ObjectType.status == "draft").limit(50)).all()
        ),
        "link_types": LinkTypeOut.model_validate(
            db.scalars(select(LinkType).where(LinkType.status == "draft").limit(50)).all()
        ),
        "objects": ObjectOut.model_validate(
            db.scalars(select(Object).where(Object.status == "draft").order_by(Object.confidence.desc()).limit(50)).all()
        ),
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
