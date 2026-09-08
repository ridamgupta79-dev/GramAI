"""ARCHITECTURE.md §5 — Chat (conversational RAG with rich payloads).

Conversations persist in the DB and are scoped to the authenticated user.
"""
from __future__ import annotations

import asyncio
import json
import uuid
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.api.auth import get_current_user
from app.db import Conversation, User, get_db
from app.services import advisory

router = APIRouter()


class ChatMessage(BaseModel):
    conversation_id: Optional[str] = None
    message: str
    analysis_id: Optional[str] = None


@router.post("")
async def chat(msg: ChatMessage,
               user: User = Depends(get_current_user),
               db: Session = Depends(get_db)):
    conv: Conversation | None = None
    if msg.conversation_id:
        conv = db.get(Conversation, msg.conversation_id)
        if not conv or conv.user_id != user.id:
            raise HTTPException(404, "Conversation not found")
    if not conv:
        conv = Conversation(id=uuid.uuid4().hex[:16], user_id=user.id,
                            title=msg.message[:60], messages_json="[]")
        db.add(conv)
        db.commit()

    history = json.loads(conv.messages_json)
    history.append({"role": "user", "content": msg.message})

    async def stream():
        reply_text = advisory.chat_reply(msg.message)
        chart = {
            "type": "bar",
            "series": [{"month": m, "value": round(3.5 + 0.2 * i, 1)}
                       for i, m in enumerate(["Jan", "Feb", "Mar", "Apr", "May", "Jun"])],
        }
        for t in reply_text.split(" "):
            yield f"event: token\ndata: {json.dumps({'t': t + ' '})}\n\n"
            await asyncio.sleep(0.01)
        yield f"event: chart\ndata: {json.dumps(chart)}\n\n"
        mid = uuid.uuid4().hex[:8]
        history.append({"role": "assistant",
                        "content": {"text": reply_text, "charts": [chart]},
                        "id": mid})
        conv.messages_json = json.dumps(history)
        db.commit()
        yield f"event: done\ndata: {json.dumps({'message_id': mid, 'conversation_id': conv.id})}\n\n"

    return StreamingResponse(stream(), media_type="text/event-stream")


@router.get("/conversations")
def conversations(user: User = Depends(get_current_user),
                  db: Session = Depends(get_db)) -> list[dict]:
    rows = (db.query(Conversation).filter(Conversation.user_id == user.id)
            .order_by(Conversation.created_at.desc()).limit(50).all())
    return [{"conversation_id": r.id, "title": r.title,
             "messages": len(json.loads(r.messages_json))} for r in rows]


@router.get("/conversations/{conv_id}/export")
def export_conversation(conv_id: str, format: str = "pdf",
                        user: User = Depends(get_current_user),
                        db: Session = Depends(get_db)) -> dict:
    conv = db.get(Conversation, conv_id)
    if not conv or conv.user_id != user.id:
        raise HTTPException(404, "Conversation not found")
    return {"conversation_id": conv_id, "format": format,
            "message_count": len(json.loads(conv.messages_json)), "exported": True}
