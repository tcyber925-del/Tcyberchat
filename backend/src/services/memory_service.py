"""
MemoryService for LangChain conversation memory management
"""

import logging
from typing import Any

from .rag_adapter import create_memory as _create_memory

logger = logging.getLogger(__name__)


def _is_human_message(msg: Any) -> bool:
    # Accept dicts with type 'human' or 'user', or objects with class name starting with 'Human'
    try:
        if isinstance(msg, dict):
            return msg.get("type") in ("human", "user")
        name = msg.__class__.__name__.lower()
        if name.startswith("human") or name in ("humanmessage", "human_message"):
            return True
        # Some LangChain message objects have .role or .type
        if getattr(msg, "role", None) == "user" or getattr(msg, "type", None) in (
            "human",
            "user",
        ):
            return True
    except Exception:
        return False
    return False


def _is_ai_message(msg: Any) -> bool:
    try:
        if isinstance(msg, dict):
            return msg.get("type") in ("ai", "assistant")
        name = msg.__class__.__name__.lower()
        if name.startswith("ai") or name in ("aimessage", "ai_message"):
            return True
        if getattr(msg, "role", None) == "assistant" or getattr(msg, "type", None) in (
            "ai",
            "assistant",
        ):
            return True
    except Exception:
        return False
    return False


class ConversationMemory:
    """Manages conversation memory for a specific conversation using LangChain"""

    def __init__(self, conversation_id: str, max_history: int = 10):
        self.conversation_id = conversation_id
        self.max_history = max_history
        # Always use the adapter to create memory; adapter will handle LangChain presence
        try:
            self.memory = _create_memory(k=max_history)
        except Exception:
            # As a last resort, use a minimal stub-like object
            class _SimpleMem:
                def __init__(self):
                    self.chat_memory = type("C", (), {"messages": []})()

            self.memory = _SimpleMem()

    def add_user_message(self, content: str):
        """Add a user message to memory"""
        # Prefer explicit chat_memory API if available
        if hasattr(self.memory, "chat_memory"):
            cm = self.memory.chat_memory
            if hasattr(cm, "add_user_message"):
                try:
                    cm.add_user_message(content)
                    return
                except Exception:
                    pass
            if hasattr(cm, "add_message"):
                try:
                    cm.add_message({"type": "human", "content": content})
                    return
                except Exception:
                    pass

        # Fallback: try to call generic methods or create a dict message
        try:
            if hasattr(self.memory.chat_memory, "add_message"):
                self.memory.chat_memory.add_message(
                    {"type": "human", "content": content}
                )
                return
        except Exception:
            pass

        # Last resort: append to messages list if present
        msgs = getattr(self.memory.chat_memory, "messages", None)
        if msgs is not None:
            msgs.append({"type": "human", "content": content})

    def add_ai_message(self, content: str):
        """Add an AI message to memory"""
        if hasattr(self.memory, "chat_memory"):
            cm = self.memory.chat_memory
            if hasattr(cm, "add_ai_message"):
                try:
                    cm.add_ai_message(content)
                    return
                except Exception:
                    pass
            if hasattr(cm, "add_message"):
                try:
                    cm.add_message({"type": "ai", "content": content})
                    return
                except Exception:
                    pass

        try:
            if hasattr(self.memory.chat_memory, "add_message"):
                self.memory.chat_memory.add_message({"type": "ai", "content": content})
                return
        except Exception:
            pass

        msgs = getattr(self.memory.chat_memory, "messages", None)
        if msgs is not None:
            msgs.append({"type": "ai", "content": content})

    def get_context(self) -> list[dict[str, str]]:
        """Get conversation context for AI processing"""
        messages = getattr(self.memory.chat_memory, "messages", [])
        context = []

        for msg in messages:
            # support dict-based stub messages and object-based messages
            if isinstance(msg, dict):
                role = "user" if msg.get("type") in ("human", "user") else "assistant"
                content = msg.get("content", "")
                context.append({"role": role, "content": content})
            else:
                # try attribute access
                try:
                    if _is_human_message(msg):
                        # try attribute access first
                        content = (
                            getattr(msg, "content", None) or msg.get("content")
                            if isinstance(msg, dict)
                            else str(msg)
                        )
                        context.append({"role": "user", "content": content})
                    elif _is_ai_message(msg):
                        content = (
                            getattr(msg, "content", None) or msg.get("content")
                            if isinstance(msg, dict)
                            else str(msg)
                        )
                        context.append({"role": "assistant", "content": content})
                    else:
                        # best effort
                        content = (
                            getattr(msg, "content", str(msg))
                            if not isinstance(msg, dict)
                            else msg.get("content", str(msg))
                        )
                        role = (
                            "user"
                            if (
                                isinstance(msg, dict)
                                and msg.get("type", "").lower() in ("human", "user")
                            )
                            else "assistant"
                        )
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
        if hasattr(self.memory, "chat_memory") and hasattr(
            self.memory.chat_memory, "clear"
        ):
            try:
                self.memory.chat_memory.clear()
                return
            except Exception:
                pass
        try:
            self.memory.clear()
        except Exception:
            msgs = getattr(self.memory.chat_memory, "messages", None)
            if msgs is not None:
                msgs.clear()


class MemoryService:
    """Service for managing conversation memories across the application"""

    def __init__(self):
        self.memories: dict[str, ConversationMemory] = {}
        self.default_max_history = 10

    def get_memory(self, conversation_id: str) -> ConversationMemory:
        """Get or create memory for a conversation"""
        if conversation_id not in self.memories:
            self.memories[conversation_id] = ConversationMemory(
                conversation_id, max_history=self.default_max_history
            )
        return self.memories[conversation_id]

    def add_message(self, conversation_id: str, role: str, content: str):
        """Add a message to conversation memory"""
        memory = self.get_memory(conversation_id)

        if role == "user":
            memory.add_user_message(content)
        elif role == "assistant" or role == "bot":
            memory.add_ai_message(content)

    def get_context(self, conversation_id: str) -> list[dict[str, str]]:
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
