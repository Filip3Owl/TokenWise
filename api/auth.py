"""
Módulo de autenticação da API TokenWise.

Duas dependências de autenticação distintas:
- require_admin_auth: valida a variável de ambiente TOKENWISE_API_KEY mestre (endpoints admin).
- require_client_auth: busca o Bearer token na tabela de clientes SQLite e
  aplica rate limits por cliente via janela deslizante em memória.
"""

import os
import time
from collections import defaultdict

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from .database import get_client_by_token

_bearer = HTTPBearer()

# Armazém de janela deslizante: id do cliente -> lista de timestamps UNIX dos últimos 60 s.
# Funciona corretamente em servidores de processo único; use Redis para implantações multi-processo.
_rate_windows: dict[str, list[float]] = defaultdict(list)


def require_admin_auth(credentials: HTTPAuthorizationCredentials = Depends(_bearer)) -> None:
    """
    Valida a variável de ambiente TOKENWISE_API_KEY mestre.
    Usada exclusivamente pelos endpoints /admin/*.
    """
    expected = os.environ.get("TOKENWISE_API_KEY", "")
    if not expected:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="TOKENWISE_API_KEY not configured on server.",
        )
    if credentials.credentials != expected:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing token.",
            headers={"WWW-Authenticate": "Bearer"},
        )


def require_client_auth(
    request: Request,
    credentials: HTTPAuthorizationCredentials = Depends(_bearer),
) -> dict:
    """
    Busca o Bearer token na tabela de clientes e aplica o rate limit por cliente.

    Retorna o dicionário do registro do cliente para que endpoints possam inspecionar plan/name se necessário.
    Levanta:
        HTTP 401 se o token não for encontrado ou estiver revogado.
        HTTP 429 se o cliente tiver excedido seu rate limit no minuto atual.
    """
    client = get_client_by_token(credentials.credentials)
    if client is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing token.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    _enforce_rate_limit(str(client["id"]), client["rate_limit"])

    # Disponibiliza o registro do cliente para o endpoint via request.state
    request.state.client = client
    return client


def _enforce_rate_limit(token: str, rate_limit: int) -> None:
    """Rate limit por janela deslizante: levanta HTTP 429 se o cliente excedeu rate_limit req/min."""
    now = time.time()
    window = _rate_windows[token]
    # Descarta timestamps com mais de 60 segundos
    window[:] = [t for t in window if now - t < 60]
    if len(window) >= rate_limit:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Rate limit exceeded. Maximum {rate_limit} requests/minute.",
            headers={"Retry-After": "60"},
        )
    window.append(now)
