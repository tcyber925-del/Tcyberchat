from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session
from ..database import get_db
from ..services.document_service import get_document_service, DocumentService
from ..models.document import Document, DocumentRead
import logging

logger = logging.getLogger(__name__)

router = APIRouter(tags=["documents"])

@router.post("/", response_model=DocumentRead)
async def upload_document(
    file: UploadFile = File(...),
    document_service: DocumentService = Depends(get_document_service),
) -> Document:
    logger.info(f"Received file upload request for: {file.filename}")
    if not file.filename:
        raise HTTPException(status_code=400, detail="No file name provided")
    try:
        file_content = await file.read()
        document = document_service.create_document(
            file_name=file.filename,
            file_content=file_content.decode('utf-8') # Assuming text content for now
        )
        logger.info(f"Document '{file.filename}' uploaded and processed with ID: {document.id}")
        return document
    except Exception as e:
        logger.error(f"Error uploading document: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to upload document: {e}")

@router.get("/{document_id}", response_model=DocumentRead)
def get_document(
    document_id: str,
    document_service: DocumentService = Depends(get_document_service),
) -> Document:
    """
    Retrieves a document by its ID.

    Args:
        document_id: The ID of the document to retrieve.
        document_service: The document service dependency.

    Returns:
        The document with the specified ID.

    Raises:
        HTTPException: If the document is not found.
    """
    logger.info(f"Fetching document with ID: {document_id}")
    document = document_service.get_document(document_id)
    if not document:
        logger.warning(f"Document with ID {document_id} not found")
        raise HTTPException(status_code=404, detail="Document not found")
    logger.info(f"Document with ID {document_id} found and returned")
    return document
