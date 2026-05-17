"""
Upstream LLM client for the TokenWise proxy (POST /chat).

Supports Anthropic (claude-*) and OpenAI (gpt-*) models.
The appropriate client is selected automatically based on the model name prefix.
API keys are read from environment variables — never hardcoded.
"""

import os
import httpx
from fastapi import HTTPException

from .config import LLM_TIMEOUT_SECONDS


def call_llm(prompt: str, model: str) -> str:
    """
    Send an optimized prompt to the appropriate upstream LLM and return its response.

    Args:
        prompt: The already-optimized prompt text.
        model:  The target model name (e.g. "claude-sonnet-4-6", "gpt-4o").

    Returns:
        The text content of the LLM's response.

    Raises:
        HTTP 400 if the model prefix is not supported.
        HTTP 500 if the upstream API key is missing or the call fails.
        HTTP 504 if the upstream LLM does not respond within LLM_TIMEOUT_SECONDS.
    """
    if model.startswith("claude"):
        return _call_anthropic(prompt, model)
    elif model.startswith("gpt") or model.startswith("o1"):
        return _call_openai(prompt, model)
    else:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported model '{model}'. Use a claude-* or gpt-* model.",
        )


def _call_anthropic(prompt: str, model: str) -> str:
    """Call the Anthropic Messages API and return the assistant's text response."""
    api_key = os.environ.get("ANTHROPIC_API_KEY", "")
    if not api_key:
        raise HTTPException(
            status_code=500,
            detail="ANTHROPIC_API_KEY is not configured on the server.",
        )

    headers = {
        "x-api-key": api_key,
        "anthropic-version": "2023-06-01",
        "content-type": "application/json",
    }
    payload = {
        "model": model,
        "max_tokens": 1024,
        "messages": [{"role": "user", "content": prompt}],
    }

    try:
        response = httpx.post(
            "https://api.anthropic.com/v1/messages",
            headers=headers,
            json=payload,
            timeout=LLM_TIMEOUT_SECONDS,
        )
        response.raise_for_status()
    except httpx.TimeoutException:
        raise HTTPException(
            status_code=504,
            detail=f"Anthropic API did not respond within {LLM_TIMEOUT_SECONDS}s.",
        )
    except httpx.HTTPStatusError as exc:
        raise HTTPException(
            status_code=502,
            detail=f"Anthropic API error: {exc.response.status_code} — {exc.response.text}",
        )

    # Extract the text from the first content block of the response
    data = response.json()
    return data["content"][0]["text"]


def _call_openai(prompt: str, model: str) -> str:
    """Call the OpenAI Chat Completions API and return the assistant's text response."""
    api_key = os.environ.get("OPENAI_API_KEY", "")
    if not api_key:
        raise HTTPException(
            status_code=500,
            detail="OPENAI_API_KEY is not configured on the server.",
        )

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
    }

    try:
        response = httpx.post(
            "https://api.openai.com/v1/chat/completions",
            headers=headers,
            json=payload,
            timeout=LLM_TIMEOUT_SECONDS,
        )
        response.raise_for_status()
    except httpx.TimeoutException:
        raise HTTPException(
            status_code=504,
            detail=f"OpenAI API did not respond within {LLM_TIMEOUT_SECONDS}s.",
        )
    except httpx.HTTPStatusError as exc:
        raise HTTPException(
            status_code=502,
            detail=f"OpenAI API error: {exc.response.status_code} — {exc.response.text}",
        )

    # Extract the text from the first choice of the response
    data = response.json()
    return data["choices"][0]["message"]["content"]
