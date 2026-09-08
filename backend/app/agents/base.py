"""Agent framework — one specialist agent per dashboard topic.

Each agent: deterministic base computation + optional LLM narrative grounded
in RAG-retrieved scheme context. If no LLM key is configured, the
deterministic part still produces a complete, useful result.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from app.services import llm_service, rag_service


@dataclass
class AgentResult:
    topic: str
    data: dict[str, Any]                      # deterministic structured output
    narrative: str = ""                       # LLM commentary (may be empty)
    sources: list[str] = field(default_factory=list)


class BaseAgent:
    """Subclasses implement compute(); optionally enrich() with the LLM."""

    topic: str = "base"
    retrieval_query: str = ""

    def run(self, ctx: dict) -> AgentResult:
        data = self.compute(ctx)
        sources: list[str] = []
        if self.retrieval_query:
            docs = rag_service.retrieve(self.retrieval_query)
            sources = [d["name"] for d in docs]
            if llm_service.llm_available():
                try:
                    data["narrative"] = self.enrich(ctx, data,
                                                    rag_service.context_for_query(self.retrieval_query))
                except Exception:
                    pass
        return AgentResult(topic=self.topic, data=data, sources=sources)

    # -- override points -------------------------------------------------
    def compute(self, ctx: dict) -> dict:
        raise NotImplementedError

    def enrich(self, ctx: dict, data: dict, rag_context: str) -> str:
        prompt = (
            f"User context: {ctx}\n\nComputed analysis (authoritative numbers):\n{data}\n\n"
            f"Government scheme reference:\n{rag_context}\n\n"
            f"Write 3-5 sentences of practical advice for a first-time rural "
            f"entrepreneur about '{self.topic}'. Use simple language. Do not invent "
            f"numbers that contradict the computed analysis."
        )
        out = llm_service.generate_json(prompt, 'Respond as {"narrative": "..."}')
        return out.get("narrative", "")
