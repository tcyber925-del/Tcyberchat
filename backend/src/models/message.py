"""
Message model for chat conversations
"""

from datetime import datetime
from typing import List, Optional
from uuid import uuid4

from sqlalchemy import Column, String, DateTime, Text, ForeignKey, JSON
from sqlalchemy.orm import relationship

from ..database import Base


class Message(Base):
    """Represents individual chat messages in conversations"""

    __tablename__ = "messages"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid4()))
    content = Column(Text, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)
    type = Column(String(50), nullable=False)  # 'user' or 'bot'
    conversation_id = Column(String(36), ForeignKey("conversations.id"), nullable=True)

    # Optional citations for RAG responses
    citations = Column(JSON, nullable=True)  # List of {"docId": uuid, "page": int, "snippet": str}

    # Optional metadata for processing details
    processing_metadata = Column(JSON, nullable=True)  # {"processing_time": float, "model_used": str, etc.}

    # Relationships
    conversation = relationship("Conversation", back_populates="messages")

    def __init__(self, content: str, type: str, conversation_id: Optional[str] = None, citations: Optional[List[dict]] = None, processing_metadata: Optional[dict] = None):
        self.content = content
        self.type = type
        self.conversation_id = conversation_id
        self.citations = citations
        self.processing_metadata = processing_metadata

    def to_dict(self) -> dict:
        """Convert to dictionary for API responses"""
        return {
            "id": str(self.id),
            "content": self.content,
            "timestamp": self.timestamp.isoformat(),
            "type": self.type,
            "conversationId": str(self.conversation_id) if self.conversation_id is not None else None,
            "citations": self.citations,
            "metadata": self.processing_metadata
        }

    def __repr__(self) -> str:
        return f"<Message(id={self.id}, type={self.type}, content='{self.content[:50]}...')>"