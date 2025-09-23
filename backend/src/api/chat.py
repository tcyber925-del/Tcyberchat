"""
Chat API endpoints
"""

from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..database import get_db
from ..services.chat_service import get_chat_service, ChatService
from ..services.rag_service import get_rag_service, RAGService
from ..models.message import Message

router = APIRouter(prefix="/chat", tags=["chat"])

@router.post("/")
async def chat(
    message: str,
    documentId: Optional[str] = None,
    db: Session = Depends(get_db)
) -> dict:
    """
    Send a chat message and get AI response.

    Supports both general conversation and document-specific queries.
    """
    if not message or not message.strip():
        raise HTTPException(status_code=422, detail="Message cannot be empty")

    chat_service = get_chat_service()
    rag_service = get_rag_service()

    try:
        # For now, create a simple conversation or use default
        # In a full implementation, this would handle conversation management
        conversation_id = "default"  # Placeholder

        # Add user message
        user_message = chat_service.add_message(
            conversation_id=conversation_id,
            content=message.strip(),
            message_type="user"
        )

        # Generate AI response
        if documentId:
            # Use RAG for document-specific queries
            rag_result = await rag_service.generate_rag_response(
                query=message,
                document_id=documentId
            )

            response_text = rag_result["response"]
            citations = rag_result.get("citations", [])

            # Add AI response with citations
            ai_message = chat_service.add_message(
                conversation_id=conversation_id,
                content=response_text,
                message_type="bot",
                citations=citations
            )
        else:
            # General conversation - would use AIService
            # For now, placeholder response
            response_text = f"I received your message: '{message}'. This is a placeholder response."
            ai_message = chat_service.add_message(
                conversation_id=conversation_id,
                content=response_text,
                message_type="bot"
            )

        return {
            "response": response_text,
            "messageId": str(ai_message.id),
            "citations": ai_message.citations if hasattr(ai_message, 'citations') else []
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Chat processing failed: {str(e)}")

@router.get("/conversations")
async def get_conversations(
    limit: int = 50,
    db: Session = Depends(get_db)
) -> list:
    """Get list of conversations"""
    chat_service = get_chat_service()
    conversations = chat_service.get_conversations(limit=limit)

    return [conv.to_dict() for conv in conversations]

@router.get("/conversations/{conversation_id}")
async def get_conversation(
    conversation_id: str,
    db: Session = Depends(get_db)
) -> dict:
    """Get a specific conversation with messages"""
    chat_service = get_chat_service()
    conversation = chat_service.get_conversation(conversation_id)

    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")

    result = conversation.to_dict()
    result["messages"] = [
        msg.to_dict() for msg in conversation.messages
    ] if conversation.messages else []

    return result

@router.delete("/conversations/{conversation_id}")
async def delete_conversation(
    conversation_id: str,
    db: Session = Depends(get_db)
) -> dict:
    """Delete a conversation"""
    chat_service = get_chat_service()
    success = chat_service.delete_conversation(conversation_id)

    if not success:
        raise HTTPException(status_code=404, detail="Conversation not found")

    return {"message": "Conversation deleted successfully"}