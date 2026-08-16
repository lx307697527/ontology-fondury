from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.modules.api import documents, objects, ontology, review, search
from app.db import Base, engine, run_legacy_migrations

app = FastAPI(title="ontology-fondry", version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(documents.router, prefix="/api/documents", tags=["documents"])
app.include_router(ontology.router, prefix="/api/ontology", tags=["ontology"])
app.include_router(objects.router, prefix="/api/objects", tags=["objects"])
app.include_router(search.router, prefix="/api/search", tags=["search"])
app.include_router(review.router, prefix="/api/review", tags=["review"])


@app.on_event("startup")
def init_db():
    Base.metadata.create_all(engine)
    run_legacy_migrations()  # 幂等补历史列（无 Alembic 期间的迁移机制）


@app.get("/api/health")
def health():
    return {"status": "ok", "service": "ontology-fondry", "version": "0.1.0"}
