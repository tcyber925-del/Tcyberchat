"""
Document model for uploaded files and processing
"""
from __future__ import annotations
from datetime import datetime
from typing import List, Optional
from uuid import uuid4

from sqlalchemy import Column, String, DateTime, Text, BigInteger, JSON, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from pydantic import BaseModel, Field
from uuid import UUID as PyUUID
from ..database import Base


class Document(Base):
    """Represents uploaded documents for processing"""

    __tablename__ = "documents"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    filename = Column(String(255), nullable=False)
    path = Column(String(500), nullable=False)  # Local file system path
    size = Column(BigInteger, nullable=False)  # File size in bytes
    mime_type = Column(String(100), nullable=False)
    uploaded_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Extracted content from various processing stages
    content = Column(Text, nullable=True)  # Text extracted from document

    # Chunking for RAG
    chunks = Column(JSON, nullable=True)  # List of text chunks

    # Vector store reference
    vector_store_id = Column(String(255), nullable=True)  # ChromaDB collection ID

    # Processing status
    status = Column(String(50), default="uploading", nullable=False)
    # Status progression: uploading -> processing -> analyzing/transcribing -> embedding -> ready

    # Audio-specific fields
    transcription = Column(Text, nullable=True)  # For audio files

    # Image-specific fields
    image_analysis = Column(JSON, nullable=True)  # AI analysis results for images/diagrams

    # Preview/thumbnail path
    preview_image = Column(String(500), nullable=True)

    def __init__(self, filename: str, path: str, size: int, mime_type: str,
                 content: Optional[str] = None, chunks: Optional[List[str]] = None,
                 transcription: Optional[str] = None, image_analysis: Optional[dict] = None,
                 status: str = "uploading"):
        self.filename = filename
        self.path = path
        self.size = size
        self.mime_type = mime_type
        self.content = content
        self.chunks = chunks
        self.transcription = transcription
        self.image_analysis = image_analysis
        self.status = status

    @property
    def is_text_document(self) -> bool:
        """Check if this is a text-based document"""
        return str(self.mime_type) in ['text/plain', 'text/markdown', 'application/pdf']

    @property
    def is_image(self) -> bool:
        """Check if this is an image file"""
        return str(self.mime_type).startswith('image/')

    @property
    def is_audio(self) -> bool:
        """Check if this is an audio file"""
        return str(self.mime_type).startswith('audio/')

    @property
    def has_content(self) -> bool:
        """Check if content has been extracted"""
        return self.content is not None

    @property
    def has_transcription(self) -> bool:
        """Check if transcription is available"""
        return self.transcription is not None

    @property
    def has_image_analysis(self) -> bool:
        """Check if image analysis is available"""
        return self.image_analysis is not None

    def to_dict(self) -> dict:
        """Convert to dictionary for API responses"""
        return {
            "id": str(self.id),
            "filename": self.filename,
            "size": self.size,
            "mimeType": self.mime_type,
            "uploadedAt": self.uploaded_at.isoformat(),
            "status": self.status,
            "hasContent": self.content is not None,
            "hasTranscription": self.transcription is not None,
            "hasImageAnalysis": self.image_analysis is not None,
            "previewImage": self.preview_image
        }

    def update_status(self, new_status: str):
        """Update processing status with validation"""
        valid_statuses = ["uploading", "processing", "analyzing", "transcribing", "embedding", "ready", "completed", "error"]
        if new_status not in valid_statuses:
            raise ValueError(f"Invalid status: {new_status}")
        self.status = new_status

    def __repr__(self) -> str:
        return f"<Document(id={self.id}, filename='{self.filename}', status='{self.status}')>"

class DocumentCreate(BaseModel):
    filename: str
    path: str
    size: int
    mime_type: str
    content: Optional[str] = None
    chunks: Optional[List[str]] = None
    transcription: Optional[str] = None
    image_analysis: Optional[dict] = None

class DocumentRead(BaseModel):
    id: PyUUID
    filename: str
    size: int
    mimeType: str = Field(alias="mime_type")
    uploadedAt: datetime = Field(alias="uploaded_at")
    status: str
    hasContent: bool = Field(alias="has_content")
    hasTranscription: bool = Field(alias="has_transcription")
    hasImageAnalysis: bool = Field(alias="has_image_analysis")
    previewImage: Optional[str] = Field(alias="preview_image")

    class Config:
        orm_mode = True
        allow_population_by_field_name = True
