"""
Conversation model for organizing chat message threads
"""

from datetime import datetime
from typing import Optional
from uuid import uuid4

from sqlalchemy import Column, String, DateTime, Text, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from ..database import Base


class Conversation(Base):
    """Represents chat sessions for organizing message threads"""

    __tablename__ = "conversations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    title = Column(String(100), nullable=False)  # Auto-generated or user-set title
    started_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    last_activity = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Optional document association for document-specific chats
    document_id = Column(UUID(as_uuid=True), ForeignKey("documents.id"), nullable=True)

    # Relationships
    messages = relationship("Message", back_populates="conversation", cascade="all, delete-orphan")
    document = relationship("Document", backref="conversations")

    def __init__(self, title: Optional[str] = None, document_id: Optional[str] = None):
        self.title = title or self._generate_default_title()
        self.document_id = document_id

    @staticmethod
    def _generate_default_title() -> str:
        """Generate a default conversation title"""
        now = datetime.utcnow()
        return f"Chat {now.strftime('%Y-%m-%d %H:%M')}"

    def update_activity(self):
        """Update the last activity timestamp"""
        self.last_activity = datetime.utcnow()

    def to_dict(self) -> dict:
        """Convert to dictionary for API responses"""
        return {
            "id": str(self.id),
            "title": self.title,
            "startedAt": self.started_at.isoformat(),
            "lastActivity": self.last_activity.isoformat(),
            "documentId": str(self.document_id) if self.document_id else None,
            "messageCount": len(self.messages) if self.messages else 0
        }

    def generate_smart_title(self) -> str:
        """Generate a smart title based on conversation content"""
        if not self.messages:
            return self.title

        # Use first user message as title (truncated)
        first_user_message = next(
            (msg for msg in self.messages if msg.type == 'user'),
            None
        )

        if first_user_message and len(first_user_message.content) > 5:
            # Truncate to first 50 characters, add ellipsis if needed
            content = first_user_message.content[:50]
            if len(first_user_message.content) > 50:
                content += "..."
            return content

        return self.title

    def __repr__(self) -> str:
        return f"<Conversation(id={self.id}, title='{self.title}', messages={len(self.messages) if self.messages else 0})>"