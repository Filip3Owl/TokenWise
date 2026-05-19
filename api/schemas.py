"""
Pydantic schemas for the TokenWise REST API.

Defines the request and response models used by the /optimize, /chat, and /admin endpoints.
Pydantic validates incoming JSON automatically and serializes responses.
"""

from pydantic import BaseModel, Field

from .config import MAX_PROMPT_CHARS


# ---------------------------------------------------------------------------
# /optimize
# ---------------------------------------------------------------------------

class OptimizeRequest(BaseModel):
    """Payload for POST /optimize."""

    text: str = Field(..., min_length=1, max_length=MAX_PROMPT_CHARS)
    model: str = "claude-sonnet-4-6"
    lang: str = "auto"
    conservative: bool = False


class StrategyResultResponse(BaseModel):
    """Per-strategy breakdown included in every OptimizeResponse."""

    name: str
    tokens_saved: int
    applied: bool


class OptimizeResponse(BaseModel):
    """Full optimization result returned by POST /optimize."""

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
    """Payload for POST /chat."""

    text: str = Field(..., min_length=1, max_length=MAX_PROMPT_CHARS)
    model: str = "claude-sonnet-4-6"
    lang: str = "auto"
    conservative: bool = False


class ChatResponse(BaseModel):
    """Response from POST /chat — LLM reply plus optimization metadata."""

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
    """Payload for POST /admin/clients."""

    name: str = Field(..., min_length=1, max_length=100)
    plan: str = Field("basic", pattern="^(basic|pro)$")
    # Optional override; if omitted the plan default is used (basic=60, pro=300)
    rate_limit: int | None = Field(None, ge=1, le=10_000)


class ClientUpdate(BaseModel):
    """Payload for PATCH /admin/clients/{token}."""

    plan: str | None = Field(None, pattern="^(basic|pro)$")
    rate_limit: int | None = Field(None, ge=1, le=10_000)


class ClientResponse(BaseModel):
    """Client record returned by admin endpoints."""

    id: int
    name: str
    token: str
    plan: str
    rate_limit: int
    is_active: bool
    created_at: str
