"""
MemoryService for LangChain conversation memory management
"""

from typing import List, Optional, Dict, Any
try:
    from langchain.memory import ConversationBufferWindowMemory
    from langchain.schema import BaseMessage, HumanMessage, AIMessage
except Exception:
    # Fallback to adapter when langchain is not installed or has different layout
    from .rag_adapter import create_memory as _create_memory
    ConversationBufferWindowMemory = None
    BaseMessage = dict
    HumanMessage = dict
    AIMessage = dict
import logging

logger = logging.getLogger(__name__)


class ConversationMemory:
    """Manages conversation memory for a specific conversation using LangChain"""

    def __init__(self, conversation_id: str, max_history: int = 10):
        self.conversation_id = conversation_id
        self.max_history = max_history
        if ConversationBufferWindowMemory is not None:
            self.memory = ConversationBufferWindowMemory(
                k=max_history,
                return_messages=True,
                memory_key="chat_history"
            )
        else:
            # Use adapter fallback memory
            self.memory = _create_memory(k=max_history)

    def add_user_message(self, content: str):
        """Add a user message to memory"""
        # Prefer explicit chat_memory API if available
        if hasattr(self.memory, 'chat_memory'):
            cm = self.memory.chat_memory
            if hasattr(cm, 'add_user_message'):
                try:
                    cm.add_user_message(content)
                    return
                except Exception:
                    pass
            if hasattr(cm, 'add_message'):
                try:
                    cm.add_message({'type': 'human', 'content': content})
                    return
                except Exception:
                    pass

        # Fallback: try to call generic methods or create a dict message
        try:
            self.memory.chat_memory.add_message(HumanMessage(content=content))
        except Exception:
            try:
                self.memory.chat_memory.add_message({'type': 'human', 'content': content})
            except Exception:
                # Last resort: append to messages list if present
                msgs = getattr(self.memory.chat_memory, 'messages', None)
                if msgs is not None:
                    msgs.append({'type': 'human', 'content': content})

    def add_ai_message(self, content: str):
        """Add an AI message to memory"""
        if hasattr(self.memory, 'chat_memory'):
            cm = self.memory.chat_memory
            if hasattr(cm, 'add_ai_message'):
                try:
                    cm.add_ai_message(content)
                    return
                except Exception:
                    pass
            if hasattr(cm, 'add_message'):
                try:
                    cm.add_message({'type': 'ai', 'content': content})
                    return
                except Exception:
                    pass

        try:
            self.memory.chat_memory.add_message(AIMessage(content=content))
        except Exception:
            try:
                self.memory.chat_memory.add_message({'type': 'ai', 'content': content})
            except Exception:
                msgs = getattr(self.memory.chat_memory, 'messages', None)
                if msgs is not None:
                    msgs.append({'type': 'ai', 'content': content})

    def get_context(self) -> List[Dict[str, str]]:
        """Get conversation context for AI processing"""
        messages = getattr(self.memory.chat_memory, 'messages', [])
        context = []

        for msg in messages:
            # support dict-based stub messages and object-based messages
            if isinstance(msg, dict):
                role = 'user' if msg.get('type') in ('human', 'user') else 'assistant'
                content = msg.get('content', '')
                context.append({"role": role, "content": content})
            else:
                # try attribute access
                try:
                    if isinstance(msg, HumanMessage):
                        context.append({"role": "user", "content": msg.content})
                    elif isinstance(msg, AIMessage):
                        context.append({"role": "assistant", "content": msg.content})
                    else:
                        # best effort
                        content = getattr(msg, 'content', str(msg))
                        role = 'user' if getattr(msg, 'type', '').lower() in ('human', 'user') else 'assistant'
                        context.append({"role": role, "content": content})
                except Exception:
                    # skip if unable to parse
                    continue

        return context

    def get_langchain_memory(self):
        """Get the underlying LangChain memory object"""
        return self.memory

    def clear(self):
        """Clear all conversation memory"""
        if hasattr(self.memory, 'chat_memory') and hasattr(self.memory.chat_memory, 'clear'):
            try:
                self.memory.chat_memory.clear()
                return
            except Exception:
                pass
        try:
            self.memory.clear()
        except Exception:
            msgs = getattr(self.memory.chat_memory, 'messages', None)
            if msgs is not None:
                msgs.clear()


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