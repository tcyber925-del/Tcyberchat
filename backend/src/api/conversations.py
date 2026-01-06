"""
Conversations API: CRUD and export/import
"""

import json

from fastapi import APIRouter, Body, Depends, HTTPException, Response, Request
from pydantic import BaseModel
from sqlalchemy.orm import Session

from ..database import get_db
from ..services.chat_service import get_chat_service
from ..auth.dependencies import get_current_user, get_current_user_optional
from ..models.user import User

router = APIRouter(tags=["conversations"])


class CreateConversationRequest(BaseModel):
    title: str | None = None
    documentId: str | None = None


class UpdateConversationRequest(BaseModel):
    title: str | None = None
    isPinned: bool | None = None
    isArchived: bool | None = None


@router.get("/")
async def list_conversations(
    request: Request,
    limit: int = 50, 
    db: Session = Depends(get_db), 
    current_user: User | None = Depends(get_current_user_optional)
):
    guest_session_id = request.headers.get("X-Guest-Session-Id")
    if not current_user and not guest_session_id:
        raise HTTPException(status_code=401, detail="Not authenticated")

    chat_service = get_chat_service(db)
    convs = chat_service.get_conversations(
        limit=limit, 
        user_id=str(current_user.id) if current_user else None,
        session_id=guest_session_id if not current_user else None
    )
    return [c.to_dict() for c in convs]


@router.post("/")
async def create_conversation(
    request: Request,
    create_request: CreateConversationRequest = Body(...), 
    db: Session = Depends(get_db), 
    current_user: User | None = Depends(get_current_user_optional)
):
    guest_session_id = request.headers.get("X-Guest-Session-Id")
    if not current_user and not guest_session_id:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    if not current_user and create_request.documentId:
        raise HTTPException(status_code=403, detail="Guests cannot link documents. Please sign up.")

    chat_service = get_chat_service(db)
    conv = chat_service.create_conversation(
        title=create_request.title, 
        document_id=create_request.documentId, 
        user_id=str(current_user.id) if current_user else None,
        session_id=guest_session_id if not current_user else None,
        is_guest=not current_user
    )
    return conv.to_dict()


@router.get("/{conversation_id}")
async def get_conversation(
    conversation_id: str, 
    request: Request,
    db: Session = Depends(get_db), 
    current_user: User | None = Depends(get_current_user_optional)
):
    guest_session_id = request.headers.get("X-Guest-Session-Id")
    if not current_user and not guest_session_id:
        raise HTTPException(status_code=401, detail="Not authenticated")

    chat_service = get_chat_service(db)
    conv = chat_service.get_conversation(
        conversation_id, 
        user_id=str(current_user.id) if current_user else None,
        session_id=guest_session_id if not current_user else None
    )
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")
    result = conv.to_dict()
    result["messages"] = [m.to_dict() for m in conv.messages] if conv.messages else []
    return result


@router.patch("/{conversation_id}")
async def update_conversation(
    conversation_id: str,
    request: Request,
    update_request: UpdateConversationRequest = Body(...),
    db: Session = Depends(get_db),
    current_user: User | None = Depends(get_current_user_optional),
):
    guest_session_id = request.headers.get("X-Guest-Session-Id")
    if not current_user and not guest_session_id:
        raise HTTPException(status_code=401, detail="Not authenticated")

    chat_service = get_chat_service(db)
    
    # Check if conversation belongs to user/guest
    conv_check = chat_service.get_conversation(
        conversation_id, 
        user_id=str(current_user.id) if current_user else None,
        session_id=guest_session_id if not current_user else None
    )
    if not conv_check:
        raise HTTPException(status_code=404, detail="Conversation not found")
        
    conv = None
    if update_request.title is not None:
        conv = chat_service.update_conversation_title(conversation_id, update_request.title)
    if update_request.isPinned is not None or update_request.isArchived is not None:
        conv = chat_service.set_conversation_flags(
            conversation_id, is_pinned=update_request.isPinned, is_archived=update_request.isArchived
        )
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return conv.to_dict()


@router.delete("/{conversation_id}")
async def delete_conversation(
    conversation_id: str, 
    request: Request,
    db: Session = Depends(get_db), 
    current_user: User | None = Depends(get_current_user_optional)
):
    guest_session_id = request.headers.get("X-Guest-Session-Id")
    if not current_user and not guest_session_id:
        raise HTTPException(status_code=401, detail="Not authenticated")

    chat_service = get_chat_service(db)
    success = chat_service.delete_conversation(
        conversation_id, 
        user_id=str(current_user.id) if current_user else None,
        session_id=guest_session_id if not current_user else None
    )
    if not success:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return {"message": "Conversation deleted"}


@router.post("/{conversation_id}/export")
async def export_conversation(
    conversation_id: str, 
    request: Request,
    db: Session = Depends(get_db), 
    current_user: User | None = Depends(get_current_user_optional)
):
    guest_session_id = request.headers.get("X-Guest-Session-Id")
    if not current_user and not guest_session_id:
        raise HTTPException(status_code=401, detail="Not authenticated")

    chat_service = get_chat_service(db)
    conv = chat_service.get_conversation(
        conversation_id, 
        user_id=str(current_user.id) if current_user else None,
        session_id=guest_session_id if not current_user else None
    )
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")
    payload = conv.to_dict()
    payload["messages"] = [m.to_dict() for m in conv.messages] if conv.messages else []
    body = json.dumps(payload, indent=2)
    return Response(content=body, media_type="application/json")
