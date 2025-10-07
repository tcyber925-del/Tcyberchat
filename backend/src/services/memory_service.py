"""
MemoryService for LangChain conversation memory management
"""

from typing import List, Optional, Dict, Any
from langchain.memory import ConversationBufferWindowMemory
from langchain.schema import BaseMessage, HumanMessage, AIMessage
import logging

logger = logging.getLogger(__name__)


class ConversationMemory:
    """Manages conversation memory for a specific conversation using LangChain"""

    def __init__(self, conversation_id: str, max_history: int = 10):
        self.conversation_id = conversation_id
        self.max_history = max_history
        self.memory = ConversationBufferWindowMemory(
            k=max_history,
            return_messages=True,
            memory_key="chat_history"
        )

    def add_user_message(self, content: str):
        """Add a user message to memory"""
        self.memory.chat_memory.add_message(HumanMessage(content=content))

    def add_ai_message(self, content: str):
        """Add an AI message to memory"""
        self.memory.chat_memory.add_message(AIMessage(content=content))

    def get_context(self) -> List[Dict[str, str]]:
        """Get conversation context for AI processing"""
        messages = self.memory.chat_memory.messages
        context = []

        for msg in messages:
            if isinstance(msg, HumanMessage):
                context.append({"role": "user", "content": msg.content})
            elif isinstance(msg, AIMessage):
                context.append({"role": "assistant", "content": msg.content})

        return context

    def get_langchain_memory(self):
        """Get the underlying LangChain memory object"""
        return self.memory

    def clear(self):
        """Clear all conversation memory"""
        self.memory.clear()


class MemoryService:
    """Service for managing conversation memories across the application"""

    def __init__(self):
        self.memories: Dict[str, ConversationMemory] = {}
        self.default_max_history = 10

    def get_memory(self, conversation_id: str) -> ConversationMemory:
        """Get or create memory for a conversation"""
        if conversation_id not in self.memories:
            self.memories[conversation_id] = ConversationMemory(
                conversation_id,
                max_history=self.default_max_history
            )
        return self.memories[conversation_id]

    def add_message(self, conversation_id: str, role: str, content: str):
        """Add a message to conversation memory"""
        memory = self.get_memory(conversation_id)

        if role == "user":
            memory.add_user_message(content)
        elif role == "assistant" or role == "bot":
            memory.add_ai_message(content)

    def get_context(self, conversation_id: str) -> List[Dict[str, str]]:
        """Get conversation context for AI processing"""
        memory = self.get_memory(conversation_id)
        return memory.get_context()

    def clear_memory(self, conversation_id: str):
        """Clear memory for a specific conversation"""
        if conversation_id in self.memories:
            self.memories[conversation_id].clear()

    def delete_memory(self, conversation_id: str):
        """Delete memory for a specific conversation"""
        if conversation_id in self.memories:
            del self.memories[conversation_id]


# Global instance
_memory_service = None

def get_memory_service() -> MemoryService:
    """Get singleton MemoryService instance"""
    global _memory_service
    if _memory_service is None:
        _memory_service = MemoryService()
    return _memory_service