"""
MediaContent model for rich content rendering in chat
"""

from uuid import uuid4
from typing import Optional

from sqlalchemy import Column, String, Text, JSON, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from ..database import Base


class MediaContent(Base):
    """Represents embedded media and rich content for chat rendering"""

    __tablename__ = "media_content"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    message_id = Column(UUID(as_uuid=True), ForeignKey("messages.id"), nullable=False)

    # Content type and data
    type = Column(String(50), nullable=False)  # 'image', 'table', 'code_block', 'diagram'
    content = Column(Text, nullable=False)  # Raw content data (HTML, Markdown, JSON)

    # Rendering metadata
    content_metadata = Column(JSON, nullable=True)  # {"dimensions": {"width": 800, "height": 600}, "syntax": "python", etc.}

    # Relationships
    message = relationship("Message", backref="media_content")

    def __init__(self, message_id: str, type: str, content: str, metadata: Optional[dict] = None):
        self.message_id = message_id
        self.type = type
        self.content = content
        self.metadata = metadata or {}

    @property
    def is_image(self) -> bool:
        """Check if this is an image content"""
        return self.type == 'image'

    @property
    def is_code_block(self) -> bool:
        """Check if this is a code block"""
        return self.type == 'code_block'

    @property
    def is_table(self) -> bool:
        """Check if this is a table"""
        return self.type == 'table'

    def to_dict(self) -> dict:
        """Convert to dictionary for API responses"""
        return {
            "id": str(self.id),
            "messageId": str(self.message_id),
            "type": self.type,
            "content": self.content,
            "metadata": self.metadata
        }

    def __repr__(self) -> str:
        return f"<MediaContent(id={self.id}, type='{self.type}', message_id={self.message_id})>"