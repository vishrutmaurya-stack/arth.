"""Groq LLM client wrapper using credentials from .env."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from dotenv import dotenv_values

ROOT = Path(__file__).resolve().parent.parent.parent

_CLIENT = None
_RESOLVED_MODEL: str | None = None


def get_llm_model() -> str:
    """Return configured Groq model from .env or os.environ."""
    global _RESOLVED_MODEL
    if _RESOLVED_MODEL is None:
        env_vals = dotenv_values(ROOT / ".env")
        model = env_vals.get("LLM_MODEL") or os.environ.get("LLM_MODEL")
        if not model:
            raise RuntimeError("LLM_MODEL is not set in .env")
        _RESOLVED_MODEL = model.strip()
    return _RESOLVED_MODEL


def get_groq_client() -> Any:
    """Return initialized Groq client."""
    global _CLIENT
    if _CLIENT is None:
        try:
            from groq import Groq
        except ImportError as exc:
            raise RuntimeError("groq package is not installed") from exc

        env_vals = dotenv_values(ROOT / ".env")
        api_key = env_vals.get("GROQ_API_KEY") or os.environ.get("GROQ_API_KEY")
        if not api_key or not api_key.strip():
            raise RuntimeError("GROQ_API_KEY is not set in .env")

        _CLIENT = Groq(api_key=api_key.strip())
    return _CLIENT


def complete(
    messages: list[dict[str, str]],
    temperature: float = 0.1,
    max_tokens: int = 500,
) -> str:
    """Execute chat completion with configured Groq model."""
    client = get_groq_client()
    model = get_llm_model()
    try:
        response = client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
        )
        content = response.choices[0].message.content or ""
        return content.strip()
    except Exception as exc:
        raise RuntimeError(f"Groq API call failed (model={model}): {exc}") from exc
