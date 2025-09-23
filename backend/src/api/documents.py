"""
Documents API endpoints for upload, management, and summarization
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, BackgroundTasks
from sqlalchemy.orm import Session

from ..database import get_db
from ..services.document_service import get_document_service, DocumentService
from ..services.ai_service import get_ai_service, AIService

router = APIRouter(prefix="/documents", tags=["documents"])

@router.post("/")
async def upload_document(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
) -> dict:
    """
    Upload a document for processing.

    Supports text, PDF, and image files.
    Processing happens asynchronously in the background.
    """
    doc_service = get_document_service()

    # Validate file
    is_valid, error_msg = doc_service.validate_file(file)
    if not is_valid:
        raise HTTPException(status_code=400, detail=error_msg)

    try:
        # Save file and create database record
        file_path = doc_service.save_uploaded_file(file)
        document = doc_service.create_document_record(
            filename=file.filename,
            file_path=file_path,
            size=len(await file.read()),
            mime_type=file.content_type
        )

        # Start async processing
        background_tasks.add_task(doc_service.process_document_async, document.id)

        return {
            "documentId": str(document.id),
            "filename": document.filename,
            "size": document.size,
            "status": document.status
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")

@router.get("/")
async def list_documents(
    status: Optional[str] = None,
    limit: int = 50,
    db: Session = Depends(get_db)
) -> List[dict]:
    """Get list of documents with optional status filter"""
    doc_service = get_document_service()
    documents = doc_service.get_documents(status=status, limit=limit)

    return [doc.to_dict() for doc in documents]

@router.delete("/{document_id}")
async def delete_document(
    document_id: str,
    db: Session = Depends(get_db)
) -> dict:
    """Delete a document and its associated files"""
    doc_service = get_document_service()
    success = doc_service.delete_document(document_id)

    if not success:
        raise HTTPException(status_code=404, detail="Document not found")

    return {"message": "Document deleted successfully"}

@router.post("/{document_id}/summarize")
async def summarize_document(
    document_id: str,
    db: Session = Depends(get_db)
) -> dict:
    """Generate AI summary of a document"""
    doc_service = get_document_service()
    ai_service = get_ai_service()

    # Check if document exists and is ready
    document = doc_service.get_document(document_id)
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")

    if document.status != "ready":
        raise HTTPException(status_code=422, detail=f"Document not ready for summarization (status: {document.status})")

    if not document.content:
        raise HTTPException(status_code=422, detail="Document has no extractable content")

    try:
        # Generate summary
        summary_result = await ai_service.generate_summary(document.content, max_length=300)

        # Store summary in database
        from ..models.summary import Summary
        summary = Summary(
            document_id=document_id,
            content=summary_result.get("summary", summary_result["response"]),
            model=summary_result.get("model", "unknown")
        )

        db.add(summary)
        db.commit()
        db.refresh(summary)

        return {
            "summary": summary.content,
            "summaryId": str(summary.id),
            "model": summary.model,
            "documentId": document_id
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Summarization failed: {str(e)}")

@router.get("/{document_id}/summaries")
async def get_document_summaries(
    document_id: str,
    db: Session = Depends(get_db)
) -> List[dict]:
    """Get all summaries for a document"""
    # Check if document exists
    doc_service = get_document_service()
    document = doc_service.get_document(document_id)
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")

    # Get summaries
    summaries = db.query(Summary).filter(Summary.document_id == document_id).all()

    return [summary.to_dict() for summary in summaries]