"""
Pydantic schemas for the TokenWise REST API.

Defines the request and response models used by the /optimize and /chat endpoints.
Pydantic validates incoming JSON automatically and serializes responses.
"""

from pydantic import BaseModel, Field

from .config import MAX_PROMPT_CHARS


class OptimizeRequest(BaseModel):
    """Payload for POST /optimize."""

    # Enforce a character cap to prevent oversized payloads from consuming LLM quota
    text: str = Field(..., min_length=1, max_length=MAX_PROMPT_CHARS)

    # Target LLM model; used for token counting and cost calculation
    model: str = "claude-sonnet-4-6"

    # Language of the prompt: "auto" triggers automatic detection via langdetect
    lang: str = "auto"

    # Conservative mode skips stopword removal to preserve more of the original meaning
    conservative: bool = False


class StrategyResultResponse(BaseModel):
    """Per-strategy breakdown included in every OptimizeResponse."""

    name: str           # Human-readable strategy name
    tokens_saved: int   # Tokens removed by this strategy (0 if not applied)
    applied: bool       # Whether the strategy made any change


class OptimizeResponse(BaseModel):
    """Full optimization result returned by POST /optimize."""

    original_text: str
    optimized_text: str

    # Token counts before and after optimization
    original_tokens: int
    final_tokens: int
    tokens_saved: int
    savings_pct: float      # Percentage of tokens saved (0–100)

    model: str
    lang: str               # Resolved language ("en" or "pt")

    # Estimated API cost in USD based on the model's input price per 1M tokens
    original_cost: float
    final_cost: float
    cost_saved: float
    cost_savings_pct: float

    # Breakdown of what each strategy contributed
    strategies: list[StrategyResultResponse]


class ChatRequest(BaseModel):
    """Payload for POST /chat."""

    # The prompt to optimize and forward to the upstream LLM
    text: str = Field(..., min_length=1, max_length=MAX_PROMPT_CHARS)

    # Target LLM — determines which upstream API is called (Anthropic or OpenAI)
    model: str = "claude-sonnet-4-6"

    # Language for the optimizer; "auto" triggers automatic detection
    lang: str = "auto"

    # Conservative mode skips stopword removal for safer optimization
    conservative: bool = False


class ChatResponse(BaseModel):
    """Response from POST /chat — LLM reply plus optimization metadata."""

    # Raw text response from the upstream LLM
    llm_response: str

    # Optimization metrics so the caller can see how much was saved
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
