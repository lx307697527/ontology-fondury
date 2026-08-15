from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.config import get_settings
from app.db import get_db
from app.models import Link, LinkType, Object, ObjectType
from app.schemas import GraphEdge, GraphNode, GraphOut, NeighborOut, ObjectDetailOut, ObjectOut

router = APIRouter()


@router.get("", response_model=list[ObjectOut])
def list_objects(
    type_name: str | None = None,
    q: str | None = None,
    status: str | None = None,
    limit: int = 100,
    db: Session = Depends(get_db),
):
    query = select(Object).order_by(Object.confidence.desc(), Object.created_at.desc())
    if type_name:
        query = query.join(ObjectType).where(ObjectType.name == type_name)
    if status:
        query = query.where(Object.status == status)
    if q:
        query = query.where(Object.title.ilike(f"%{q}%"))
    return db.scalars(query.limit(min(limit, 500))).all()


@router.get("/graph", response_model=GraphOut)
def get_graph(limit: int | None = None, db: Session = Depends(get_db)):
    cap = min(limit or get_settings().max_objects_per_graph, 1000)
    ranked = (
        select(Object.id, func.count(Link.id).label("degree"))
        .outerjoin(Link, or_(Link.source_object_id == Object.id, Link.target_object_id == Object.id))
        .group_by(Object.id)
        .subquery()
    )
    ids = db.scalars(
        select(ranked.c.id).order_by(ranked.c.degree.desc(), ranked.c.id).limit(cap)
    ).all()
    if not ids:
        return GraphOut(nodes=[], edges=[])
    nodes = db.scalars(select(Object).where(Object.id.in_(ids))).all()
    types = {t.id: t for t in db.scalars(select(ObjectType)).all()}
    edges = db.scalars(
        select(Link).where(or_(Link.source_object_id.in_(ids), Link.target_object_id.in_(ids)))
    ).all()
    link_types = {lt.id: lt for lt in db.scalars(select(LinkType)).all()}
    kept_ids = {o.id for o in nodes}
    return GraphOut(
        nodes=[
            GraphNode(
                id=o.id,
                title=o.title,
                object_type_id=o.object_type_id,
                object_type_name=types[o.object_type_id].name if o.object_type_id in types else "",
                provenance=o.provenance,
                confidence=o.confidence,
            )
            for o in nodes
        ],
        edges=[
            GraphEdge(
                id=e.id,
                link_type_id=e.link_type_id,
                link_type_name=link_types[e.link_type_id].name if e.link_type_id in link_types else "",
                source=e.source_object_id,
                target=e.target_object_id,
                confidence=e.confidence,
            )
            for e in edges
            if e.source_object_id in kept_ids and e.target_object_id in kept_ids
        ],
    )


@router.get("/{object_id}", response_model=ObjectDetailOut)
def get_object(object_id: str, db: Session = Depends(get_db)):
    obj = db.get(Object, object_id)
    if obj is None:
        raise HTTPException(404, "object not found")
    rows = db.execute(
        select(Link, LinkType, Object)
        .join(LinkType, Link.link_type_id == LinkType.id)
        .join(Object, or_(Link.source_object_id == Object.id, Link.target_object_id == Object.id))
        .where(or_(Link.source_object_id == object_id, Link.target_object_id == object_id))
        .where(Object.id != object_id)
        .limit(200)
    ).all()
    neighbors = [
        NeighborOut(
            link_type_id=link.link_type_id,
            link_type_name=link_type.name,
            direction="out" if link.source_object_id == object_id else "in",
            object=ObjectOut.model_validate(other),
        )
        for link, link_type, other in rows
    ]
    return ObjectDetailOut(**ObjectOut.model_validate(obj).model_dump(), neighbors=neighbors)
