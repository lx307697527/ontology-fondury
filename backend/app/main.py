from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.modules.api import documents, objects, ontology, review, search
from app.db import Base, engine

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


@app.get("/api/health")
def health():
    return {"status": "ok", "service": "ontology-fondry", "version": "0.1.0"}
