"""
Conversations API: CRUD and export/import
"""
import json
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Body, Response
from pydantic import BaseModel
from sqlalchemy.orm import Session

from ..database import get_db
from ..services.chat_service import get_chat_service, ChatService

router = APIRouter(tags=["conversations"])


class CreateConversationRequest(BaseModel):
    title: Optional[str] = None
    documentId: Optional[str] = None


class UpdateConversationRequest(BaseModel):
    title: Optional[str] = None
    isPinned: Optional[bool] = None
    isArchived: Optional[bool] = None


@router.get("/")
async def list_conversations(limit: int = 50, db: Session = Depends(get_db)):
    chat_service = get_chat_service()
    convs = chat_service.get_conversations(limit=limit)
    return [c.to_dict() for c in convs]


@router.post("/")
async def create_conversation(request: CreateConversationRequest = Body(...), db: Session = Depends(get_db)):
    chat_service = get_chat_service()
    conv = chat_service.create_conversation(title=request.title, document_id=request.documentId)
    return conv.to_dict()


@router.get("/{conversation_id}")
async def get_conversation(conversation_id: str, db: Session = Depends(get_db)):
    chat_service = get_chat_service()
    conv = chat_service.get_conversation(conversation_id)
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")
    result = conv.to_dict()
    result["messages"] = [m.to_dict() for m in conv.messages] if conv.messages else []
    return result


@router.patch("/{conversation_id}")
async def update_conversation(conversation_id: str, request: UpdateConversationRequest = Body(...), db: Session = Depends(get_db)):
    chat_service = get_chat_service()
    conv = None
    if request.title is not None:
        conv = chat_service.update_conversation_title(conversation_id, request.title)
    if request.isPinned is not None or request.isArchived is not None:
        conv = chat_service.set_conversation_flags(conversation_id, is_pinned=request.isPinned, is_archived=request.isArchived)
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return conv.to_dict()


@router.delete("/{conversation_id}")
async def delete_conversation(conversation_id: str, db: Session = Depends(get_db)):
    chat_service = get_chat_service()
    success = chat_service.delete_conversation(conversation_id)
    if not success:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return {"message": "Conversation deleted"}


@router.post("/{conversation_id}/export")
async def export_conversation(conversation_id: str, db: Session = Depends(get_db)):
    chat_service = get_chat_service()
    conv = chat_service.get_conversation(conversation_id)
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")
    payload = conv.to_dict()
    payload["messages"] = [m.to_dict() for m in conv.messages] if conv.messages else []
    body = json.dumps(payload, indent=2)
    return Response(content=body, media_type="application/json")
