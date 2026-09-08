"""Conversational follow-up Q&A grounded in the generated report."""
from __future__ import annotations

from typing import Optional

from fastapi import APIRouter
from pydantic import BaseModel

from app.services import llm_service

router = APIRouter()


class ChatRequest(BaseModel):
    question: str
    report_context: Optional[dict] = None
    language: str = "English"


class ChatResponse(BaseModel):
    answer: str


SYSTEM = ("You are a patient rural business advisor. Answer using the provided "
          "feasibility report context when relevant. Reply in {language}. Keep answers "
          "short, practical and jargon-free.")


@router.post("", response_model=ChatResponse)
def chat(req: ChatRequest) -> ChatResponse:
    if not llm_service.llm_available():
        return ChatResponse(
            answer="AI chat requires an LLM API key (set LLM_API_KEY). "
                   "The feasibility report and finance calculator work offline."
        )
    ctx = ""
    if req.report_context:
        import json
        ctx = "Feasibility report context:\n" + json.dumps(
            req.report_context, ensure_ascii=False)[:6000]
    answer = llm_service.generate_json(
        f"{ctx}\n\nQuestion: {req.question}",
        SYSTEM.format(language=req.language) +
        ' Respond as {"answer": "..."}',
    )
    return ChatResponse(answer=answer.get("answer", ""))
