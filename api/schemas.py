"""
Schemas Pydantic para a API REST do TokenWise.

Define os modelos de requisição e resposta usados pelos endpoints /optimize, /chat e /admin.
O Pydantic valida o JSON recebido automaticamente e serializa as respostas.
"""

from pydantic import BaseModel, Field

from .config import MAX_PROMPT_CHARS


# ---------------------------------------------------------------------------
# /optimize
# ---------------------------------------------------------------------------

class OptimizeRequest(BaseModel):
    """Payload do POST /optimize."""

    text: str = Field(..., min_length=1, max_length=MAX_PROMPT_CHARS)
    model: str = "claude-sonnet-4-6"
    lang: str = "auto"
    conservative: bool = False


class StrategyResultResponse(BaseModel):
    """Breakdown por estratégia incluído em todo OptimizeResponse."""

    name: str
    tokens_saved: int
    applied: bool


class OptimizeResponse(BaseModel):
    """Resultado completo de otimização retornado pelo POST /optimize."""

    original_text: str
    optimized_text: str
    original_tokens: int
    final_tokens: int
    tokens_saved: int
    savings_pct: float
    model: str
    lang: str
    original_cost: float
    final_cost: float
    cost_saved: float
    cost_savings_pct: float
    strategies: list[StrategyResultResponse]


# ---------------------------------------------------------------------------
# /chat
# ---------------------------------------------------------------------------

class ChatRequest(BaseModel):
    """Payload do POST /chat."""

    text: str = Field(..., min_length=1, max_length=MAX_PROMPT_CHARS)
    model: str = "claude-sonnet-4-6"
    lang: str = "auto"
    conservative: bool = False


class ChatResponse(BaseModel):
    """Resposta do POST /chat — resposta do LLM mais metadados de otimização."""

    llm_response: str
    original_tokens: int
    final_tokens: int
    tokens_saved: int
    savings_pct: float
    original_cost: float
    final_cost: float
    cost_saved: float
    cost_savings_pct: float
    model: str
    lang: str


# ---------------------------------------------------------------------------
# /admin/clients
# ---------------------------------------------------------------------------

class ClientCreate(BaseModel):
    """Payload do POST /admin/clients."""

    name: str = Field(..., min_length=1, max_length=100)
    plan: str = Field("basic", pattern="^(basic|pro)$")
    # Substituição opcional; se omitido, usa o padrão do plano (basic=60, pro=300)
    rate_limit: int | None = Field(None, ge=1, le=10_000)


class ClientUpdate(BaseModel):
    """Payload do PATCH /admin/clients/{token}."""

    plan: str | None = Field(None, pattern="^(basic|pro)$")
    rate_limit: int | None = Field(None, ge=1, le=10_000)


class ClientResponse(BaseModel):
    """Registro de cliente retornado pelos endpoints de administração."""

    id: int
    name: str
    token: str
    plan: str
    rate_limit: int
    is_active: bool
    created_at: str
