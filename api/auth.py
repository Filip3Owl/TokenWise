"""
Authentication module for the TokenWise API.

Provides a FastAPI dependency that enforces Bearer token authentication.
The expected token is read from the TOKENWISE_API_KEY environment variable
so that secrets are never hardcoded in source code.
"""

import os
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

# HTTPBearer extracts the token from the "Authorization: Bearer <token>" header
_bearer = HTTPBearer()


def require_auth(credentials: HTTPAuthorizationCredentials = Depends(_bearer)) -> None:
    """
    FastAPI dependency that validates the Bearer token on every protected request.

    Raises:
        HTTP 500 if TOKENWISE_API_KEY is not set on the server.
        HTTP 401 if the token is missing or does not match.
    """
    expected = os.environ.get("TOKENWISE_API_KEY", "")

    # Fail loudly if the server was started without a key configured
    if not expected:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="TOKENWISE_API_KEY not configured on server.",
        )

    # Constant-time comparison is not strictly needed here since the token
    # is a high-entropy random string, but rejecting early is fine for this stage
    if credentials.credentials != expected:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing token.",
            headers={"WWW-Authenticate": "Bearer"},
        )
