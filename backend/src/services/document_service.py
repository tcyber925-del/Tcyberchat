"""
DocumentService for file upload, processing, and management
"""

import os
import shutil
from pathlib import Path
from typing import List, Optional, Tuple
from uuid import uuid4
import asyncio

from sqlalchemy.orm import Session
from fastapi import UploadFile

from ..database import get_db
from ..models.document import Document


class DocumentService:
    """Service for managing document upload, processing, and storage"""

    # Supported MIME types
    SUPPORTED_TEXT_TYPES = ['text/plain', 'text/markdown', 'application/pdf']
    SUPPORTED_IMAGE_TYPES = ['image/jpeg', 'image/png', 'image/gif', 'image/webp']
    SUPPORTED_AUDIO_TYPES = ['audio/mpeg', 'audio/wav', 'audio/ogg', 'audio/mp4']

    MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB
    MAX_IMAGE_SIZE = 10 * 1024 * 1024  # 10MB for images
    MAX_AUDIO_SIZE = 10 * 1024 * 1024  # 10MB for audio

    def __init__(self, db: Session, upload_dir: str = "uploads"):
        self.db = db
        self.upload_dir = Path(upload_dir)
        self.upload_dir.mkdir(exist_ok=True)

    def validate_file(self, file: UploadFile) -> Tuple[bool, Optional[str]]:
        """Validate uploaded file type and size"""
        # Check file size
        if hasattr(file, 'size') and file.size:
            max_size = self._get_max_size_for_mime_type(file.content_type)
            if file.size > max_size:
                return False, f"File too large. Maximum size: {max_size // (1024*1024)}MB"

        # Check MIME type
        if file.content_type not in self._get_supported_types():
            return False, f"Unsupported file type: {file.content_type}"

        return True, None

    def _get_max_size_for_mime_type(self, mime_type: str) -> int:
        """Get maximum file size for MIME type"""
        if mime_type.startswith('image/'):
            return self.MAX_IMAGE_SIZE
        elif mime_type.startswith('audio/'):
            return self.MAX_AUDIO_SIZE
        else:
            return self.MAX_FILE_SIZE

    def _get_supported_types(self) -> List[str]:
        """Get all supported MIME types"""
        return self.SUPPORTED_TEXT_TYPES + self.SUPPORTED_IMAGE_TYPES + self.SUPPORTED_AUDIO_TYPES

    def save_uploaded_file(self, file: UploadFile) -> str:
        """Save uploaded file and return file path"""
        file_id = str(uuid4())
        file_extension = Path(file.filename).suffix if file.filename else ""

        # Create subdirectory structure for organization
        subdir = self.upload_dir / file_id[:2] / file_id[2:4]
        subdir.mkdir(parents=True, exist_ok=True)

        file_path = subdir / f"{file_id}{file_extension}"

        # Save file
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        return str(file_path)

    def create_document_record(self, filename: str, file_path: str, size: int,
                             mime_type: str) -> Document:
        """Create database record for uploaded document"""
        document = Document(
            filename=filename,
            path=file_path,
            size=size,
            mime_type=mime_type
        )

        self.db.add(document)
        self.db.commit()
        self.db.refresh(document)

        return document

    def get_document(self, document_id: str) -> Optional[Document]:
        """Get document by ID"""
        return self.db.query(Document).filter(Document.id == document_id).first()

    def get_documents(self, status: Optional[str] = None, limit: int = 50) -> List[Document]:
        """Get documents with optional status filter"""
        query = self.db.query(Document)
        if status:
            query = query.filter(Document.status == status)
        return query.order_by(Document.uploaded_at.desc()).limit(limit).all()

    def update_document_status(self, document_id: str, status: str) -> Optional[Document]:
        """Update document processing status"""
        document = self.get_document(document_id)
        if document:
            document.update_status(status)
            self.db.commit()
            self.db.refresh(document)
        return document

    def delete_document(self, document_id: str) -> bool:
        """Delete document and its file"""
        document = self.get_document(document_id)
        if document:
            # Delete file from disk
            try:
                if os.path.exists(document.path):
                    os.remove(document.path)
            except OSError:
                pass  # File may not exist or can't be deleted

            # Delete database record
            self.db.delete(document)
            self.db.commit()
            return True
        return False

    async def process_document_async(self, document_id: str) -> None:
        """Async processing pipeline for documents"""
        document = self.get_document(document_id)
        if not document:
            return

        try:
            # Update status to processing
            document.update_status("processing")

            # Extract text content based on file type
            if document.is_text_document:
                await self._extract_text_content(document)
            elif document.is_image:
                await self._process_image(document)
            elif document.is_audio:
                await self._transcribe_audio(document)

            # Generate chunks for RAG
            if document.content:
                await self._generate_chunks(document)

            # Update status to ready
            document.update_status("ready")

        except Exception as e:
            document.update_status("error")
            # Log error would go here

        self.db.commit()

    async def _extract_text_content(self, document: Document) -> None:
        """Extract text from text-based documents"""
        # Placeholder for text extraction logic
        # In real implementation, would use libraries like PyPDF2, python-docx, etc.
        document.content = f"Extracted content from {document.filename}"

    async def _process_image(self, document: Document) -> None:
        """Process image files (OCR, analysis)"""
        # Placeholder for image processing
        document.content = f"Image content from {document.filename}"

    async def _transcribe_audio(self, document: Document) -> None:
        """Transcribe audio files"""
        # Placeholder for audio transcription
        document.transcription = f"Transcription of {document.filename}"

    async def _generate_chunks(self, document: Document) -> None:
        """Generate text chunks for RAG"""
        # Placeholder chunking logic
        if document.content:
            # Simple sentence-based chunking
            sentences = document.content.split('.')
            chunks = []
            current_chunk = ""

            for sentence in sentences:
                if len(current_chunk + sentence) > 1000:  # Chunk size limit
                    if current_chunk:
                        chunks.append(current_chunk.strip())
                    current_chunk = sentence
                else:
                    current_chunk += sentence + "."

            if current_chunk:
                chunks.append(current_chunk.strip())

            document.chunks = chunks


# Dependency injection function
def get_document_service(db: Session = next(get_db())) -> DocumentService:
    """Get DocumentService instance with database session"""
    return DocumentService(db)