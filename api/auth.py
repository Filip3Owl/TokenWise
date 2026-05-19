"""
Authentication module for the TokenWise API.

Two distinct auth dependencies:
- require_admin_auth: validates the master TOKENWISE_API_KEY env var (admin endpoints).
- require_client_auth: looks up the Bearer token in the SQLite clients table and
  enforces per-client rate limits via an in-memory sliding window.
"""

import os
import time
from collections import defaultdict

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from .database import get_client_by_token

_bearer = HTTPBearer()

# Sliding-window store: client id -> list of UNIX timestamps within the last 60 s.
# Works correctly for a single-process server; use Redis for multi-process deployments.
_rate_windows: dict[str, list[float]] = defaultdict(list)


def require_admin_auth(credentials: HTTPAuthorizationCredentials = Depends(_bearer)) -> None:
    """
    Validates the master TOKENWISE_API_KEY env var.
    Used exclusively by /admin/* endpoints.
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
    Looks up the Bearer token in the clients table and enforces the per-client rate limit.

    Returns the client record dict so endpoints can inspect plan/name if needed.
    Raises:
        HTTP 401 if the token is not found or revoked.
        HTTP 429 if the client has exceeded its rate limit for the current minute.
    """
    client = get_client_by_token(credentials.credentials)
    if client is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing token.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    _enforce_rate_limit(str(client["id"]), client["rate_limit"])

    # Make the client record available to the endpoint via request.state
    request.state.client = client
    return client


def _enforce_rate_limit(token: str, rate_limit: int) -> None:
    """Sliding-window rate limit: raises HTTP 429 if the client exceeded rate_limit req/min."""
    now = time.time()
    window = _rate_windows[token]
    # Discard timestamps older than 60 seconds
    window[:] = [t for t in window if now - t < 60]
    if len(window) >= rate_limit:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Rate limit exceeded. Maximum {rate_limit} requests/minute.",
            headers={"Retry-After": "60"},
        )
    window.append(now)
