"""
ChatService for conversation and message management
"""

from typing import List, Optional, Union, cast
from uuid import UUID
from sqlalchemy.orm import Session
from sqlalchemy import desc
from sqlalchemy.orm.attributes import InstrumentedAttribute

from ..database import get_db
from ..models.message import Message
from ..models.conversation import Conversation


class ChatService:
    """Service for managing chat conversations and messages"""

    def __init__(self, db: Session):
        self.db = db

    def create_conversation(self, title: Optional[str] = None, document_id: Optional[str] = None) -> Conversation:
        """Create a new conversation"""
        conversation = Conversation(title=title, document_id=document_id)
        self.db.add(conversation)
        self.db.commit()
        self.db.refresh(conversation)
        return conversation

    def get_conversation(self, conversation_id: Optional[Union[str, UUID]]) -> Optional[Conversation]:
        """Get a conversation by ID with messages"""
        conversation_id = str(conversation_id) if conversation_id is not None else None
        return self.db.query(Conversation).filter(Conversation.id == conversation_id).first()

    def get_conversations(self, limit: int = 50) -> List[Conversation]:
        """Get all conversations ordered by last activity"""
        # cast InstrumentedAttribute to satisfy static type checkers
        last_activity_attr = cast(InstrumentedAttribute, Conversation.last_activity)
        return self.db.query(Conversation).order_by(desc(last_activity_attr)).limit(limit).all()

    def add_message(self, conversation_id: Optional[Union[str, UUID]], content: str, message_type: str,
                    citations: Optional[List[dict]] = None,
                    metadata: Optional[dict] = None) -> Message:
        """Add a message to a conversation"""
        conversation_id = str(conversation_id) if conversation_id is not None else None
        message = Message(
            conversation_id=conversation_id,
            content=content,
            type=message_type,
            citations=citations,
            processing_metadata=metadata,
        )

        self.db.add(message)

        # Update conversation last activity
        conversation = self.db.query(Conversation).filter(Conversation.id == conversation_id).first()
        if conversation:
            conversation.update_activity()
            # Generate smart title if this is the first user message
            if message_type == 'user' and len(conversation.messages) == 0:
                # use setter to avoid assigning Column objects directly
                conversation.title = conversation.generate_smart_title()

        self.db.commit()
        self.db.refresh(message)
        return message

    def get_messages(self, conversation_id: Optional[Union[str, UUID]], limit: int = 100) -> List[Message]:
        """Get messages for a conversation"""
        if conversation_id is None:
            return []
        conv_id_str: str = str(conversation_id)
        return self.db.query(Message).filter_by(conversation_id=conv_id_str).order_by(Message.timestamp.asc()).limit(limit).all()

    def get_conversation_messages(self, conversation_id: Optional[Union[str, UUID]], limit: int = 100) -> List[Message]:
        """Get messages for a conversation (alias for get_messages)"""
        return self.get_messages(conversation_id, limit)

    def update_conversation_title(self, conversation_id: Optional[Union[str, UUID]], title: str) -> Optional[Conversation]:
        """Update conversation title"""
        conversation = self.get_conversation(conversation_id)
        if conversation:
            conversation.title = title
            self.db.commit()
            self.db.refresh(conversation)
        return conversation

    def set_conversation_flags(self, conversation_id: Optional[Union[str, UUID]], *, is_pinned: Optional[bool] = None, is_archived: Optional[bool] = None) -> Optional[Conversation]:
        conversation = self.get_conversation(conversation_id)
        if not conversation:
            return None
        if is_pinned is not None:
            setattr(conversation, 'is_pinned', bool(is_pinned))
        if is_archived is not None:
            setattr(conversation, 'is_archived', bool(is_archived))
        self.db.commit()
        self.db.refresh(conversation)
        return conversation

    def set_conversation_metrics(self, conversation_id: Optional[Union[str, UUID]], metrics: dict) -> Optional[Conversation]:
        conversation = self.get_conversation(conversation_id)
        if not conversation:
            return None
        setattr(conversation, 'metrics', metrics)
        self.db.commit()
        self.db.refresh(conversation)
        return conversation

    def update_message(self, message_id: Optional[Union[str, UUID]], **fields) -> Optional[Message]:
        """Update an existing message's fields (content, citations, metadata)."""
        message_id = str(message_id) if message_id is not None else None
        message = self.db.query(Message).filter(Message.id == message_id).first()
        if not message:
            return None
        for k, v in fields.items():
            if hasattr(message, k):
                setattr(message, k, v)
        self.db.commit()
        self.db.refresh(message)
        return message

    def delete_conversation(self, conversation_id: Optional[Union[str, UUID]]) -> bool:
        """Delete a conversation and all its messages"""
        conversation = self.get_conversation(conversation_id)
        if conversation:
            self.db.delete(conversation)
            self.db.commit()
            return True
        return False

    def search_conversations(self, query: str, limit: int = 20) -> List[Conversation]:
        """Search conversations by title"""
        title_attr = cast(InstrumentedAttribute, Conversation.title)
        last_activity_attr = cast(InstrumentedAttribute, Conversation.last_activity)
        return self.db.query(Conversation).filter(title_attr.ilike(f"%{query}%")).order_by(desc(last_activity_attr)).limit(limit).all()


# Dependency injection function
def get_chat_service(db: Session = next(get_db())) -> ChatService:
    """Get ChatService instance with database session"""
    return ChatService(db)