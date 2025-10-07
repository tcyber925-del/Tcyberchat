"""
Chat API endpoints
"""

import logging
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Body
from pydantic import BaseModel
from sqlalchemy.orm import Session
from uuid import UUID
from sse_starlette.sse import EventSourceResponse

from ..database import get_db
from ..services.chat_service import get_chat_service, ChatService
from ..services.ai_service import get_ai_service, AIService
from ..services.rag_service import get_rag_service, RAGService
from ..services.memory_service import get_memory_service, MemoryService
from ..models.message import Message

logger = logging.getLogger(__name__)

class ChatRequest(BaseModel):
    message: str
    conversationId: Optional[str] = None
    documentId: Optional[str] = None
    model: Optional[str] = None

router = APIRouter(tags=["chat"])

@router.post("/")
async def chat(
    request: ChatRequest = Body(...),
    db: Session = Depends(get_db)
) -> dict:
    """
    Send a chat message and get AI response.

    Supports both general conversation and document-specific queries.
    """
    if not request.message or not request.message.strip():
        raise HTTPException(status_code=422, detail="Message cannot be empty")

    chat_service = get_chat_service()
    ai_service = get_ai_service(request.model)
    rag_service = get_rag_service()
    memory_service = get_memory_service()

    logger.info(f"Chat request: message='{request.message}', conversationId={request.conversationId}, documentId={request.documentId}, model={request.model}")
    logger.info(f"Ollama available: {ai_service.client is not None}")
    logger.info(f"Selected model: {ai_service.model_name}")
    logger.info(f"Available models: {ai_service.get_available_models()}")

    try:
        # Handle conversation management
        conversation_id = request.conversationId
        if not conversation_id:
            # Create a new conversation if none provided
            conversation = chat_service.create_conversation()
            conversation_id = str(conversation.id)  # Convert to string
        else:
            conversation_id = str(UUID(conversation_id))  # Validate and convert to string

        print(f"DEBUG: request.conversationId: {request.conversationId}, type: {type(request.conversationId)}")
        print(f"DEBUG: Conversation ID: {conversation_id}, type: {type(conversation_id)}")

        # Add user message
        user_message = chat_service.add_message(
            conversation_id=conversation_id,
            content=request.message.strip(),
            message_type="user"
        )

        # Generate AI response
        if request.documentId:
            # Use RAG for document-specific queries
            rag_result = await rag_service.generate_rag_response(
                query=request.message,
                document_id=request.documentId
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
            # General conversation - use AIService with LangChain conversation memory
            try:
                # Load existing conversation history into memory
                conversation_obj = chat_service.get_conversation(conversation_id)
                if conversation_obj and conversation_obj.messages:
                    # Load messages into memory service (excluding the current user message)
                    sorted_messages = sorted(conversation_obj.messages, key=lambda m: m.timestamp)
                    for msg in sorted_messages[:-1]:  # Exclude the last message (current user message)
                        memory_service.add_message(str(conversation_obj.id), msg.type, msg.content)

                # Add current user message to memory
                memory_service.add_message(conversation_id, "user", request.message.strip())

                # Get conversation context from memory and convert to string format
                context_dicts = memory_service.get_context(conversation_id)
                context_messages = []
                for msg in context_dicts:
                    role = msg.get("role", "unknown")
                    content = msg.get("content", "")
                    if role == "user":
                        context_messages.append(f"User: {content}")
                    elif role == "assistant":
                        context_messages.append(f"Assistant: {content}")

                # Generate AI response with context
                logger.info("Attempting to generate AI response with LangChain memory context...")
                logger.info(f"Prompt: '{request.message.strip()}'")
                logger.info(f"Context messages: {len(context_messages)}")
                ai_result = await ai_service.generate_response(
                    prompt=request.message.strip(),
                    context=context_messages if context_messages else None
                )
                logger.info(f"Successfully generated AI response: {ai_result}")

                response_text = ai_result["response"]

                # Add AI response to memory
                memory_service.add_message(conversation_id, "assistant", response_text)

                processing_metadata = {
                    "model": ai_result.get("model", "unknown"),
                    "processing_time": ai_result.get("processing_time", 0),
                    "tokens_used": ai_result.get("eval_count", 0),
                    "context_messages": len(context_messages),
                    "provider": ai_result.get("provider", "unknown")
                }

                logger.info(f"AI response generated: model={processing_metadata['model']}, provider={processing_metadata['provider']}, time={processing_metadata['processing_time']:.2f}s")

                ai_message = chat_service.add_message(
                    conversation_id=conversation_id,
                    content=response_text,
                    message_type="bot",
                    metadata=processing_metadata
                )

            except Exception as e:
                logger.error(f"AI service error: {str(e)}")
                # Fallback to simple acknowledgment
                response_text = f"I understand you said: '{request.message}'. I'm currently experiencing technical difficulties with my AI processing. Please try again later."
                ai_message = chat_service.add_message(
                    conversation_id=conversation_id,
                    content=response_text,
                    message_type="bot",
                    metadata={"error": str(e), "fallback": True}
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

@router.post("/stream")
async def chat_stream(
    request: ChatRequest = Body(...),
    db: Session = Depends(get_db)
):
    """
    Send a chat message and get streaming AI response.

    Supports both general conversation and document-specific queries.
    Returns Server-Sent Events (SSE) stream.
    """
    if not request.message or not request.message.strip():
        raise HTTPException(status_code=422, detail="Message cannot be empty")

    chat_service = get_chat_service()
    ai_service = get_ai_service(request.model)
    rag_service = get_rag_service()
    memory_service = get_memory_service()

    logger.info(f"Streaming chat request: message='{request.message}', conversationId={request.conversationId}, documentId={request.documentId}, model={request.model}")

    try:
        # Handle conversation management
        conversation_id = request.conversationId
        if not conversation_id:
            # Create a new conversation if none provided
            conversation = chat_service.create_conversation()
            conversation_id = str(conversation.id)
        else:
            conversation_id = str(UUID(conversation_id))

        # Add user message
        user_message = chat_service.add_message(
            conversation_id=conversation_id,
            content=request.message.strip(),
            message_type="user"
        )

        # Handle document-specific queries with streaming
        if request.documentId:
            full_response = ""
            ai_message = None
            citations = []

            async def generate_rag_stream():
                nonlocal full_response, ai_message, citations
                try:
                    async for chunk_data in rag_service.generate_rag_streaming_response(
                        query=request.message,
                        document_id=request.documentId
                    ):
                        if "content" in chunk_data:
                            full_response += chunk_data["content"]
                            yield {
                                "event": "chunk",
                                "data": {
                                    "content": chunk_data["content"],
                                    "done": False
                                }
                            }
                        if "citations" in chunk_data:
                            citations = chunk_data["citations"] # Update citations as they come

                    # Add AI response to database after stream completes
                    ai_message = chat_service.add_message(
                        conversation_id=conversation_id,
                        content=full_response,
                        message_type="bot",
                        citations=citations,
                        metadata={"streaming": True, "rag_enabled": True}
                    )

                    # Send completion event
                    yield {
                        "event": "message",
                        "data": {
                            "content": full_response,
                            "done": True,
                            "messageId": str(ai_message.id) if ai_message else None,
                            "citations": citations
                        }
                    }

                except Exception as e:
                    logger.error(f"Streaming RAG error: {str(e)}")
                    yield {
                        "event": "error",
                        "data": {
                            "error": str(e),
                            "done": True
                        }
                    }
            return EventSourceResponse(generate_rag_stream())

        else:
            # General conversation with streaming
            try:
                # Load existing conversation history into memory
                conversation_obj = chat_service.get_conversation(conversation_id)
                if conversation_obj and conversation_obj.messages:
                    # Load messages into memory service (excluding the current user message)
                    sorted_messages = sorted(conversation_obj.messages, key=lambda m: m.timestamp)
                    for msg in sorted_messages[:-1]:  # Exclude the last message (current user message)
                        memory_service.add_message(str(conversation_obj.id), msg.type, msg.content)

                # Add current user message to memory
                memory_service.add_message(conversation_id, "user", request.message.strip())

                # Get conversation context from memory and convert to string format
                context_dicts = memory_service.get_context(conversation_id)
                context_messages = []
                for msg in context_dicts:
                    role = msg.get("role", "unknown")
                    content = msg.get("content", "")
                    if role == "user":
                        context_messages.append(f"User: {content}")
                    elif role == "assistant":
                        context_messages.append(f"Assistant: {content}")

                # Stream the response
                full_response = ""
                ai_message = None

                async def generate():
                    nonlocal full_response, ai_message

                    try:
                        async for chunk in ai_service.generate_streaming_response(
                            prompt=request.message.strip(),
                            context=context_messages if context_messages else None
                        ):
                            full_response += chunk
                            yield {
                                "event": "chunk",
                                "data": {
                                    "content": chunk,
                                    "done": False
                                }
                            }

                        # Add AI response to memory
                        memory_service.add_message(conversation_id, "assistant", full_response)

                        # Save to database
                        ai_message = chat_service.add_message(
                            conversation_id=conversation_id,
                            content=full_response,
                            message_type="bot",
                            metadata={"streaming": True}
                        )

                        # Send completion event
                        yield {
                            "event": "message",
                            "data": {
                                "content": full_response,
                                "done": True,
                                "messageId": str(ai_message.id) if ai_message else None,
                                "citations": []
                            }
                        }

                    except Exception as e:
                        logger.error(f"Streaming error: {str(e)}")
                        yield {
                            "event": "error",
                            "data": {
                                "error": str(e),
                                "done": True
                            }
                        }

                return EventSourceResponse(generate())

            except Exception as e:
                logger.error(f"Streaming setup error: {str(e)}")
                raise HTTPException(status_code=500, detail=f"Streaming setup failed: {str(e)}")

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Streaming chat processing failed: {str(e)}")
