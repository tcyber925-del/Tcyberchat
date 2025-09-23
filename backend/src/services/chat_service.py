"""
ChatService for conversation and message management
"""

from typing import List, Optional
from uuid import UUID
from sqlalchemy.orm import Session

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

    def get_conversation(self, conversation_id: str) -> Optional[Conversation]:
        """Get a conversation by ID with messages"""
        return self.db.query(Conversation).filter(
            Conversation.id == conversation_id
        ).first()

    def get_conversations(self, limit: int = 50) -> List[Conversation]:
        """Get all conversations ordered by last activity"""
        return self.db.query(Conversation).order_by(
            Conversation.last_activity.desc()
        ).limit(limit).all()

    def add_message(self, conversation_id: str, content: str, message_type: str,
                   citations: Optional[List[dict]] = None,
                   metadata: Optional[dict] = None) -> Message:
        """Add a message to a conversation"""
        message = Message(
            conversation_id=conversation_id,
            content=content,
            type=message_type,
            citations=citations,
            processing_metadata=metadata
        )

        self.db.add(message)

        # Update conversation last activity
        conversation = self.db.query(Conversation).filter(
            Conversation.id == conversation_id
        ).first()
        if conversation:
            conversation.update_activity()
            # Generate smart title if this is the first user message
            if message_type == 'user' and len(conversation.messages) == 0:
                conversation.title = conversation.generate_smart_title()

        self.db.commit()
        self.db.refresh(message)
        return message

    def get_messages(self, conversation_id: str, limit: int = 100) -> List[Message]:
        """Get messages for a conversation"""
        return self.db.query(Message).filter(
            Message.conversation_id == conversation_id
        ).order_by(Message.timestamp.asc()).limit(limit).all()

    def get_conversation_messages(self, conversation_id: str, limit: int = 100) -> List[Message]:
        """Get messages for a conversation (alias for get_messages)"""
        return self.get_messages(conversation_id, limit)

    def update_conversation_title(self, conversation_id: str, title: str) -> Optional[Conversation]:
        """Update conversation title"""
        conversation = self.get_conversation(conversation_id)
        if conversation:
            conversation.title = title
            self.db.commit()
            self.db.refresh(conversation)
        return conversation

    def delete_conversation(self, conversation_id: str) -> bool:
        """Delete a conversation and all its messages"""
        conversation = self.get_conversation(conversation_id)
        if conversation:
            self.db.delete(conversation)
            self.db.commit()
            return True
        return False

    def search_conversations(self, query: str, limit: int = 20) -> List[Conversation]:
        """Search conversations by title"""
        return self.db.query(Conversation).filter(
            Conversation.title.ilike(f"%{query}%")
        ).order_by(Conversation.last_activity.desc()).limit(limit).all()


# Dependency injection function
def get_chat_service(db: Session = next(get_db())) -> ChatService:
    """Get ChatService instance with database session"""
    return ChatService(db)