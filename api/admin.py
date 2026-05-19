"""
Admin router for managing per-client API tokens.

All endpoints require the master TOKENWISE_API_KEY (Bearer token from env var).
Clients can be created, listed, updated, and revoked without restarting the server.
"""

from fastapi import APIRouter, Depends, HTTPException, status

from .auth import require_admin_auth
from .database import create_client, list_clients, revoke_client, update_client
from .schemas import ClientCreate, ClientResponse, ClientUpdate

router = APIRouter(prefix="/admin", tags=["admin"])


@router.post("/clients", response_model=ClientResponse, status_code=status.HTTP_201_CREATED)
def create_client_endpoint(
    body: ClientCreate,
    _: None = Depends(require_admin_auth),
):
    """Create a new client and return its generated Bearer token."""
    try:
        client = create_client(name=body.name, plan=body.plan, rate_limit=body.rate_limit)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc))
    return ClientResponse(**client)


@router.get("/clients", response_model=list[ClientResponse])
def list_clients_endpoint(_: None = Depends(require_admin_auth)):
    """Return all clients (active and revoked) ordered by creation date."""
    return [ClientResponse(**c) for c in list_clients()]


@router.patch("/clients/{token}", response_model=ClientResponse)
def update_client_endpoint(
    token: str,
    body: ClientUpdate,
    _: None = Depends(require_admin_auth),
):
    """Update a client's plan and/or rate_limit."""
    try:
        client = update_client(token=token, plan=body.plan, rate_limit=body.rate_limit)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc))
    if client is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Client not found.")
    return ClientResponse(**client)


@router.delete("/clients/{token}", status_code=status.HTTP_204_NO_CONTENT)
def revoke_client_endpoint(token: str, _: None = Depends(require_admin_auth)):
    """Revoke a client token (soft-delete). Returns 204 on success, 404 if not found."""
    if not revoke_client(token):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Client not found or already revoked.")
