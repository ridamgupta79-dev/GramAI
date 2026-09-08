"""RAG-lite scheme knowledge base.

Retrieves relevant government-scheme passages using keyword/TF scoring.
Designed so the retrieval layer can be swapped for a vector DB (ChromaDB)
without changing callers.
"""
from __future__ import annotations

import json
import os
import re
from functools import lru_cache

_DOCS_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "scheme_docs.json")

STOP = {"the", "a", "an", "of", "for", "and", "or", "to", "in", "on", "is", "are",
        "with", "as", "by", "at", "be", "up"}


def _tokens(text: str) -> list[str]:
    return [t for t in re.findall(r"[a-z0-9]+", text.lower()) if t not in STOP]


@lru_cache
def _load_docs() -> list[dict]:
    path = os.path.abspath(_DOCS_PATH)
    if not os.path.exists(path):
        return []
    with open(path, encoding="utf-8") as f:
        return json.load(f)["schemes"]


def retrieve(query: str, top_k: int = 3) -> list[dict]:
    """Return the most relevant scheme docs for a query, best first."""
    q_tokens = _tokens(query)
    scored: list[tuple[float, dict]] = []
    for doc in _load_docs():
        d_text = f"{doc['name']} {doc['text']}"
        d_tokens = _tokens(d_text)
        d_set = set(d_tokens)
        score = sum(1 for t in q_tokens if t in d_set)
        # boost name matches
        score += 3 * sum(1 for t in _tokens(doc["name"]) if t in q_tokens)
        # light coverage normalisation
        if d_tokens:
            score /= max(len(q_tokens), 1) ** 0.5
        scored.append((score, doc))
    scored.sort(key=lambda x: -x[0])
    return [doc for s, doc in scored[:top_k] if s > 0]


def context_for_query(query: str, top_k: int = 3) -> str:
    docs = retrieve(query, top_k)
    return "\n\n".join(f"[{d['name']} — {d['source']}]\n{d['text']}" for d in docs)
