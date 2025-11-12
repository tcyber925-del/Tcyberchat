"""
Conversation model for organizing chat message threads
"""

from datetime import UTC, datetime
from uuid import uuid4

from sqlalchemy import JSON, Boolean, Column, DateTime, ForeignKey, String
from sqlalchemy.orm import relationship

from ..database import Base


class Conversation(Base):
    """Represents chat sessions for organizing message threads"""

    __tablename__ = "conversations"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid4()))
    title = Column(String(100), nullable=False)  # Auto-generated or user-set title
    started_at = Column(DateTime, default=lambda: datetime.now(UTC), nullable=False)
    last_activity = Column(DateTime, default=lambda: datetime.now(UTC), nullable=False)

    # Conversation state flags
    is_pinned = Column(Boolean, default=False, nullable=False)
    is_archived = Column(Boolean, default=False, nullable=False)

    # Metrics and participants metadata
    metrics = Column(JSON, nullable=True)  # e.g. {"tokens": 123, "messages": 4}
    participants = Column(JSON, nullable=True)  # e.g. ["user", "assistant"]

    # Retention/policy string (simple representation)
    retention_policy = Column(String(100), nullable=True)

    # Optional document association for document-specific chats
    document_id = Column(String(36), ForeignKey("documents.id"), nullable=True)

    # Relationships
    messages = relationship(
        "Message", back_populates="conversation", cascade="all, delete-orphan"
    )
    document = relationship("Document", backref="conversations")

    def __init__(self, title: str | None = None, document_id: str | None = None):
        self.title = title or self._generate_default_title()
        self.document_id = document_id

    @staticmethod
    def _generate_default_title() -> str:
        """Generate a default conversation title"""
        now = datetime.now(UTC)
        return f"Chat {now.strftime('%Y-%m-%d %H:%M')}"

    def update_activity(self):
        """Update the last activity timestamp"""
        self.last_activity = datetime.now(UTC)

    def to_dict(self) -> dict:
        """Convert to dictionary for API responses"""
        started = getattr(self, "started_at", None)
        last_act = getattr(self, "last_activity", None)
        doc_id = getattr(self, "document_id", None)
        title = getattr(self, "title", "")

        return {
            "id": str(getattr(self, "id", "")),
            "title": str(title),
            "startedAt": started.isoformat() if started is not None else None,
            "lastActivity": last_act.isoformat() if last_act is not None else None,
            "documentId": str(doc_id) if doc_id is not None else None,
            "messageCount": len(getattr(self, "messages", []) or []),
            "isPinned": bool(getattr(self, "is_pinned", False)),
            "isArchived": bool(getattr(self, "is_archived", False)),
            "metrics": getattr(self, "metrics", None),
            "participants": getattr(self, "participants", None),
            "retentionPolicy": getattr(self, "retention_policy", None),
        }

    def generate_smart_title(self) -> str:
        """Generate a smart title based on conversation content"""
        if not self.messages:
            return str(getattr(self, "title", ""))

        # Use first user message as title (truncated)
        first_user_message = next(
            (msg for msg in self.messages if msg.type == "user"), None
        )

        if first_user_message and len(first_user_message.content) > 5:
            # Truncate to first 50 characters, add ellipsis if needed
            content = first_user_message.content[:50]
            if len(first_user_message.content) > 50:
                content += "..."
            return str(content)

        return str(getattr(self, "title", ""))

    def __repr__(self) -> str:
        return f"<Conversation(id={self.id}, title='{self.title}', messages={len(self.messages) if self.messages else 0})>"
