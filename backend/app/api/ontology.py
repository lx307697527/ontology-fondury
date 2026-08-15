from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import get_db
from app.models import AuditLog, LinkType, ObjectType
from app.schemas import LinkTypeIn, LinkTypeOut, ObjectTypeIn, ObjectTypeOut

router = APIRouter()


@router.get("/object-types", response_model=list[ObjectTypeOut])
def list_object_types(status: str | None = None, db: Session = Depends(get_db)):
    query = select(ObjectType).order_by(ObjectType.created_at)
    if status:
        query = query.where(ObjectType.status == status)
    return db.scalars(query).all()


@router.post("/object-types", response_model=ObjectTypeOut, status_code=201)
def create_object_type(payload: ObjectTypeIn, db: Session = Depends(get_db)):
    if db.scalar(select(ObjectType).where(ObjectType.name == payload.name)):
        raise HTTPException(409, f"object type 已存在：{payload.name}")
    obj_type = ObjectType(
        **payload.model_dump(),
        properties=[p.model_dump() for p in payload.properties],
        status="approved",
        provenance="human",
    )
    db.add(obj_type)
    db.add(AuditLog(action="create", entity="object_type", entity_id=obj_type.id, detail=payload.model_dump(mode="json")))
    db.commit()
    return obj_type


@router.patch("/object-types/{type_id}", response_model=ObjectTypeOut)
def update_object_type(type_id: str, payload: dict, db: Session = Depends(get_db)):
    obj_type = db.get(ObjectType, type_id)
    if obj_type is None:
        raise HTTPException(404, "object type not found")
    allowed = {"display_name", "description", "properties", "status"}
    changes = {k: v for k, v in payload.items() if k in allowed}
    for k, v in changes.items():
        setattr(obj_type, k, v)
    db.add(AuditLog(action="update", entity="object_type", entity_id=type_id, detail=changes))
    db.commit()
    return obj_type


@router.get("/link-types", response_model=list[LinkTypeOut])
def list_link_types(status: str | None = None, db: Session = Depends(get_db)):
    query = select(LinkType).order_by(LinkType.created_at)
    if status:
        query = query.where(LinkType.status == status)
    return db.scalars(query).all()


@router.post("/link-types", response_model=LinkTypeOut, status_code=201)
def create_link_type(payload: LinkTypeIn, db: Session = Depends(get_db)):
    if db.scalar(select(LinkType).where(LinkType.name == payload.name)):
        raise HTTPException(409, f"link type 已存在：{payload.name}")
    if db.get(ObjectType, payload.source_object_type_id) is None or db.get(ObjectType, payload.target_object_type_id) is None:
        raise HTTPException(400, "source/target object type 不存在")
    link_type = LinkType(**payload.model_dump(), status="approved", provenance="human")
    db.add(link_type)
    db.add(AuditLog(action="create", entity="link_type", entity_id=link_type.id, detail=payload.model_dump(mode="json")))
    db.commit()
    return link_type
