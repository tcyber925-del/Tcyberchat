"""
Summary model for AI-generated document summaries
"""

from datetime import UTC, datetime
from uuid import uuid4

from sqlalchemy import Column, DateTime, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from ..database import Base


class Summary(Base):
    """Represents AI-generated summaries of documents"""

    __tablename__ = "summaries"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    document_id = Column(UUID(as_uuid=True), ForeignKey("documents.id"), nullable=False)
    content = Column(Text, nullable=False)  # The summary text
    created_at = Column(DateTime, default=lambda: datetime.now(UTC), nullable=False)
    model = Column(String(100), nullable=False)  # AI model used (e.g., "llama3.1:8b")

    # Relationships
    document = relationship("Document", backref="summaries")

    def __init__(self, document_id: str, content: str, model: str = "llama3.1:8b"):
        self.document_id = document_id
        self.content = content
        self.model = model

    def to_dict(self) -> dict:
        """Convert to dictionary for API responses"""
        return {
            "id": str(self.id),
            "documentId": str(self.document_id),
            "content": self.content,
            "createdAt": self.created_at.isoformat(),
            "model": self.model,
        }

    def __repr__(self) -> str:
        return f"<Summary(id={self.id}, document_id={self.document_id}, model='{self.model}')>"
