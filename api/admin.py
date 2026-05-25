"""
Roteador de administração para gerenciar tokens de API por cliente.

Todos os endpoints exigem o TOKENWISE_API_KEY mestre (Bearer token via variável de ambiente).
Clientes podem ser criados, listados, atualizados e revogados sem reiniciar o servidor.
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
    """Cria um novo cliente e retorna seu Bearer token gerado."""
    try:
        client = create_client(name=body.name, plan=body.plan, rate_limit=body.rate_limit)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc))
    return ClientResponse(**client)


@router.get("/clients", response_model=list[ClientResponse])
def list_clients_endpoint(_: None = Depends(require_admin_auth)):
    """Retorna todos os clientes (ativos e revogados) ordenados por data de criação."""
    return [ClientResponse(**c) for c in list_clients()]


@router.patch("/clients/{token}", response_model=ClientResponse)
def update_client_endpoint(
    token: str,
    body: ClientUpdate,
    _: None = Depends(require_admin_auth),
):
    """Atualiza o plan e/ou rate_limit de um cliente."""
    try:
        client = update_client(token=token, plan=body.plan, rate_limit=body.rate_limit)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc))
    if client is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Client not found.")
    return ClientResponse(**client)


@router.delete("/clients/{token}", status_code=status.HTTP_204_NO_CONTENT)
def revoke_client_endpoint(token: str, _: None = Depends(require_admin_auth)):
    """Revoga um token de cliente (soft-delete). Retorna 204 em sucesso, 404 se não encontrado."""
    if not revoke_client(token):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Client not found or already revoked.")
