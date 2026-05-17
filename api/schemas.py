"""
Pydantic schemas for the TokenWise REST API.

Defines the request and response models used by the /optimize and /chat endpoints.
Pydantic validates incoming JSON automatically and serializes responses.
"""

from pydantic import BaseModel, Field


class OptimizeRequest(BaseModel):
    """Payload for POST /optimize."""

    # The prompt text to be optimized — must not be empty
    text: str = Field(..., min_length=1)

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
