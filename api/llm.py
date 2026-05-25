"""
Cliente LLM upstream para o proxy do TokenWise (POST /chat).

Suporta modelos Anthropic (claude-*), OpenAI (gpt-*) e Google Gemini (gemini-*).
O cliente adequado é selecionado automaticamente com base no prefixo do nome do modelo.
As chaves de API são lidas de variáveis de ambiente — nunca embutidas no código.
"""

import os
import httpx
from fastapi import HTTPException

from .config import LLM_TIMEOUT_SECONDS


def call_llm(prompt: str, model: str) -> str:
    """
    Envia um prompt otimizado ao LLM upstream adequado e retorna sua resposta.

    Args:
        prompt: O texto do prompt já otimizado.
        model:  O nome do modelo alvo (ex: "claude-sonnet-4-6", "gpt-4o").

    Returns:
        O conteúdo de texto da resposta do LLM.

    Raises:
        HTTP 400 se o prefixo do modelo não for suportado.
        HTTP 500 se a chave de API upstream estiver ausente ou a chamada falhar.
        HTTP 504 se o LLM upstream não responder dentro de LLM_TIMEOUT_SECONDS.
    """
    if model.startswith("claude"):
        return _call_anthropic(prompt, model)
    elif model.startswith("gpt") or model.startswith("o1"):
        return _call_openai(prompt, model)
    elif model.startswith("gemini"):
        return _call_gemini(prompt, model)
    else:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported model '{model}'. Use a claude-*, gpt-*, or gemini-* model.",
        )


def _call_anthropic(prompt: str, model: str) -> str:
    """Chama a Anthropic Messages API e retorna a resposta de texto do assistente."""
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

    # Extrai o texto do primeiro bloco de conteúdo da resposta
    data = response.json()
    return data["content"][0]["text"]


def _call_openai(prompt: str, model: str) -> str:
    """Chama a OpenAI Chat Completions API e retorna a resposta de texto do assistente."""
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

    # Extrai o texto da primeira escolha da resposta
    data = response.json()
    return data["choices"][0]["message"]["content"]


def _call_gemini(prompt: str, model: str) -> str:
    """
    Chama a API generateContent do Google Gemini e retorna a resposta de texto do modelo.

    Usa a API REST diretamente via httpx — sem dependência de SDK.
    Requer que GOOGLE_API_KEY esteja definida no ambiente.
    """
    api_key = os.environ.get("GOOGLE_API_KEY", "")
    if not api_key:
        raise HTTPException(
            status_code=500,
            detail="GOOGLE_API_KEY is not configured on the server.",
        )

    # Endpoint REST do Gemini: o nome do modelo faz parte do caminho da URL
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
    }

    try:
        response = httpx.post(
            url,
            params={"key": api_key},
            json=payload,
            timeout=LLM_TIMEOUT_SECONDS,
        )
        response.raise_for_status()
    except httpx.TimeoutException:
        raise HTTPException(
            status_code=504,
            detail=f"Gemini API did not respond within {LLM_TIMEOUT_SECONDS}s.",
        )
    except httpx.HTTPStatusError as exc:
        raise HTTPException(
            status_code=502,
            detail=f"Gemini API error: {exc.response.status_code} — {exc.response.text}",
        )

    # Extrai o texto da primeira parte do primeiro candidato
    data = response.json()
    return data["candidates"][0]["content"]["parts"][0]["text"]
