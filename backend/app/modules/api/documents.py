from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, UploadFile
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import get_db
from app.models import Document
from app.schemas import DocumentOut, ProcessResult
from app.modules.services import parsing
from app.modules.services.pipeline import run_pipeline

router = APIRouter()


@router.post("", response_model=DocumentOut)
def upload_document(file: UploadFile, db: Session = Depends(get_db)):
    data = file.file.read()
    doc = Document(filename=file.filename or "untitled", mime_type=file.content_type or "")
    try:
        doc.raw_text = parsing.extract_text(doc.filename, data)
        doc.status = "parsed"
    except ValueError as e:
        doc.error = str(e)
    db.add(doc)
    db.commit()
    return doc


@router.get("", response_model=list[DocumentOut])
def list_documents(db: Session = Depends(get_db)):
    return db.scalars(select(Document).order_by(Document.created_at.desc())).all()


@router.get("/{document_id}", response_model=DocumentOut)
def get_document(document_id: str, db: Session = Depends(get_db)):
    doc = db.get(Document, document_id)
    if doc is None:
        raise HTTPException(404, "document not found")
    return doc


@router.post("/{document_id}/process", response_model=ProcessResult)
def process_document(document_id: str, background: BackgroundTasks, db: Session = Depends(get_db)):
    doc = db.get(Document, document_id)
    if doc is None:
        raise HTTPException(404, "document not found")
    if not doc.raw_text:
        raise HTTPException(400, "文档解析失败或无文本内容，无法处理")
    doc.status, doc.error = "processing", ""
    db.commit()
    background.add_task(run_pipeline, document_id)
    return ProcessResult(document_id=document_id, status="processing")


@router.delete("/{document_id}")
def delete_document(document_id: str, db: Session = Depends(get_db)):
    doc = db.get(Document, document_id)
    if doc is None:
        raise HTTPException(404, "document not found")
    db.delete(doc)
    db.commit()
    return {"deleted": document_id}
