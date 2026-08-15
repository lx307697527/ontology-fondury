from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import get_db
from app.models import Chunk, Document, Object, ObjectType
from app.schemas import SearchHit

router = APIRouter()


@router.get("", response_model=list[SearchHit])
def search(q: str, limit: int = 20, db: Session = Depends(get_db)):
    pattern = f"%{q}%"
    hits: list[SearchHit] = []

    object_rows = db.execute(
        select(Object, ObjectType).join(ObjectType).where(Object.title.ilike(pattern)).limit(limit)
    ).all()
    for obj, obj_type in object_rows:
        hits.append(
            SearchHit(
                kind="object",
                id=obj.id,
                title=obj.title,
                snippet=str(obj.properties)[:200],
                object_type_name=obj_type.name,
            )
        )

    chunk_rows = db.execute(
        select(Chunk, Document)
        .join(Document, Chunk.document_id == Document.id)
        .where(Chunk.text.ilike(pattern))
        .limit(limit)
    ).all()
    for chunk, doc in chunk_rows:
        pos = chunk.text.lower().find(q.lower())
        start = max(0, pos - 60)
        snippet = ("..." if start > 0 else "") + chunk.text[start : start + 160] + "..."
        hits.append(SearchHit(kind="chunk", id=chunk.id, title=doc.filename, snippet=snippet))
    return hits
