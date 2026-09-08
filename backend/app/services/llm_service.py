"""LLM adapter — env-configurable provider (OpenAI-compatible by default).

Falls back to a deterministic template generator when no API key is set,
so the app is fully demoable offline.
"""
from __future__ import annotations

import json
import os
from typing import Any

PROVIDER = os.getenv("LLM_PROVIDER", "openai")
API_KEY = os.getenv("LLM_API_KEY", "")
MODEL = os.getenv("LLM_MODEL", "gpt-4o-mini")
BASE_URL = os.getenv("LLM_BASE_URL", "https://api.openai.com/v1")


def llm_available() -> bool:
    return bool(API_KEY)


def generate_json(prompt: str, system: str) -> dict[str, Any]:
    """Call the configured LLM and parse a JSON object from its reply."""
    if not llm_available():
        raise RuntimeError("LLM not configured")
    try:
        from openai import OpenAI
    except ImportError as e:
        raise RuntimeError("Install 'openai' package to use LLM features") from e

    client = OpenAI(api_key=API_KEY, base_url=BASE_URL)
    resp = client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": prompt},
        ],
        response_format={"type": "json_object"},
        temperature=0.4,
    )
    return json.loads(resp.choices[0].message.content or "{}")
