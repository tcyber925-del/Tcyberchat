"""
Data management API endpoints for export and import operations
"""

import json
import zipfile
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Body
from pydantic import BaseModel, validator
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
import io

from ..database import get_db
from ..models.message import Message
from ..models.conversation import Conversation
from ..models.document import Document
from ..models.summary import Summary

router = APIRouter(prefix="", tags=["data-management"])

@router.post("/export")
async def export_data(
    request: Optional[dict] = Body(None),
    db: Session = Depends(get_db),
) -> StreamingResponse:
    """
    Export conversations, documents, and metadata as a ZIP file.

    Supports filtering by date range and optional content inclusion.
    """
    try:
        # Parse and validate request body
        include_documents = True
        include_embeddings = False
        start_dt = None
        end_dt = None
        if request:
            include_documents = bool(request.get("includeDocuments", True))
            include_embeddings = bool(request.get("includeEmbeddings", False))
            date_range = request.get("dateRange") or {}
            start = date_range.get("start")
            end = date_range.get("end")
            if start and end:
                start_dt = datetime.fromisoformat(start)
                end_dt = datetime.fromisoformat(end)
                if end_dt < start_dt:
                    # raise HTTPException which should be returned as 422 by the framework
                    raise HTTPException(status_code=422, detail="Invalid date range: end before start")

        # Collect data
        export_data = {
            "metadata": {
                "export_date": datetime.utcnow().isoformat(),
                "version": "1.0.0",
                "include_documents": include_documents,
                "include_embeddings": include_embeddings,
                "date_range": {
                    "start": start,
                    "end": end
                }
            },
            "conversations": [],
            "documents": [],
            "messages": [],
            "summaries": []
        }

        # Export conversations
        conversations = db.query(Conversation).all()
        for conv in conversations:
            conv_data = conv.to_dict()
            # Filter by date if specified (use getattr to avoid Column objects)
            conv_started = getattr(conv, 'started_at', None)
            if start_dt and isinstance(conv_started, datetime) and conv_started < start_dt:
                continue
            if end_dt and isinstance(conv_started, datetime) and conv_started > end_dt:
                continue
            export_data["conversations"].append(conv_data)

        # Export messages
        messages = db.query(Message).all()
        for msg in messages:
            msg_data = msg.to_dict()
            export_data["messages"].append(msg_data)

        # Export documents (without large files unless requested)
        documents = db.query(Document).all()
        for doc in documents:
            doc_data = doc.to_dict()
            # Filter by date if specified
            doc_uploaded = getattr(doc, 'uploaded_at', None)
            if start_dt and isinstance(doc_uploaded, datetime) and doc_uploaded < start_dt:
                continue
            if end_dt and isinstance(doc_uploaded, datetime) and doc_uploaded > end_dt:
                continue

            # Remove file path from export (files are separate)
            doc_data.pop("path", None)
            export_data["documents"].append(doc_data)

        # Export summaries
        summaries = db.query(Summary).all()
        for summary in summaries:
            summary_data = summary.to_dict()
            export_data["summaries"].append(summary_data)

        # Create ZIP file in memory
        zip_buffer = io.BytesIO()

        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            # Add JSON data
            json_data = json.dumps(export_data, indent=2, default=str)
            zip_file.writestr("data.json", json_data)

            # Add document files if requested
            if include_documents:
                for doc in documents:
                    doc_path = getattr(doc, 'path', None)
                    if doc_path and Path(str(doc_path)).exists():
                        # Add file to ZIP with relative path
                        zip_file.write(str(doc_path), f"documents/{getattr(doc, 'filename', 'file')}")

        zip_buffer.seek(0)

        # Generate filename
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        filename = f"chatbot_export_{timestamp}.zip"

        return StreamingResponse(
            io.BytesIO(zip_buffer.getvalue()),
            media_type="application/zip",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )

    except HTTPException:
        # Re-raise HTTP errors so FastAPI returns proper status code
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Export failed: {str(e)}")

@router.post("/import")
async def import_data(
    file: UploadFile = File(...),
    overwrite: bool = False,
    db: Session = Depends(get_db)
) -> dict:
    """
    Import data from an exported ZIP file.

    Supports optional overwrite of existing data.
    """
    filename = getattr(file, 'filename', None)
    if not filename or not isinstance(filename, str) or not filename.endswith('.zip'):
        raise HTTPException(status_code=400, detail="File must be a ZIP archive")

    try:
        # Read ZIP file
        zip_content = await file.read()
        zip_buffer = io.BytesIO(zip_content)

        imported_counts = {
            "conversations": 0,
            "messages": 0,
            "documents": 0,
            "summaries": 0
        }
        skipped = {
            "duplicates": 0,
            "errors": 0
        }

        with zipfile.ZipFile(zip_buffer, 'r') as zip_file:
            # Read data.json
            if "data.json" not in zip_file.namelist():
                raise HTTPException(status_code=400, detail="Invalid export file: missing data.json")

            with zip_file.open("data.json") as f:
                import_data = json.loads(f.read().decode('utf-8'))

            # Import conversations
            for conv_data in import_data.get("conversations", []):
                try:
                    # Check if conversation exists
                    existing = db.query(Conversation).filter(
                        Conversation.id == conv_data["id"]
                    ).first()

                    if existing and not overwrite:
                        skipped["duplicates"] += 1
                        continue

                    if existing:
                        # Update existing
                        existing.title = conv_data["title"]
                    else:
                        # Create new
                        conv = Conversation(
                            title=conv_data["title"]
                        )
                        conv.id = conv_data["id"]  # Override auto-generated ID
                        db.add(conv)
                        imported_counts["conversations"] += 1

                except Exception as e:
                    skipped["errors"] += 1
                    continue

            # Import messages
            for msg_data in import_data.get("messages", []):
                try:
                    # Check if message exists
                    existing = db.query(Message).filter(
                        Message.id == msg_data["id"]
                    ).first()

                    if existing and not overwrite:
                        skipped["duplicates"] += 1
                        continue

                    if not existing:
                        msg = Message(
                            conversation_id=msg_data["conversationId"],
                            content=msg_data["content"],
                            type=msg_data["type"]
                        )
                        msg.id = msg_data["id"]  # Override auto-generated ID
                        db.add(msg)
                        imported_counts["messages"] += 1

                except Exception as e:
                    skipped["errors"] += 1
                    continue

            # Import documents (metadata only - files would need separate handling)
            for doc_data in import_data.get("documents", []):
                try:
                    # Check if document exists
                    existing = db.query(Document).filter(
                        Document.id == doc_data["id"]
                    ).first()

                    if existing and not overwrite:
                        skipped["duplicates"] += 1
                        continue

                    if not existing:
                        # Create document record (without file path)
                        doc = Document(
                            filename=doc_data["filename"],
                            path="",  # Would need to be set when restoring files
                            size=doc_data["size"],
                            mime_type=doc_data.get("mimeType", "application/octet-stream")
                        )
                        doc.id = doc_data["id"]  # Override auto-generated ID
                        db.add(doc)
                        imported_counts["documents"] += 1

                except Exception as e:
                    skipped["errors"] += 1
                    continue

            # Import summaries
            for summary_data in import_data.get("summaries", []):
                try:
                    # Check if summary exists
                    existing = db.query(Summary).filter(
                        Summary.id == summary_data["id"]
                    ).first()

                    if existing and not overwrite:
                        skipped["duplicates"] += 1
                        continue

                    if not existing:
                        summary = Summary(
                            document_id=summary_data["documentId"],
                            content=summary_data["content"],
                            model=summary_data.get("model", "unknown")
                        )
                        summary.id = summary_data["id"]  # Override auto-generated ID
                        db.add(summary)
                        imported_counts["summaries"] += 1

                except Exception as e:
                    skipped["errors"] += 1
                    continue

        db.commit()

        return {
            "message": "Import completed successfully",
            "imported": imported_counts,
            "skipped": skipped
        }

    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON in export file")
    except zipfile.BadZipFile:
        raise HTTPException(status_code=400, detail="Invalid ZIP file")
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Import failed: {str(e)}")

@router.get("/backup/status")
async def get_backup_status() -> dict:
    """
    Get the status of automated backups.

    Placeholder for future backup functionality.
    """
    return {
        "last_backup": None,
        "next_backup": None,
        "backup_size": 0,
        "status": "not_configured",
        "note": "Automated backups not yet implemented"
    }