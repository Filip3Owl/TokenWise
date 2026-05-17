from pydantic import BaseModel, Field


class OptimizeRequest(BaseModel):
    text: str = Field(..., min_length=1)
    model: str = "claude-sonnet-4-6"
    lang: str = "auto"
    conservative: bool = False


class StrategyResultResponse(BaseModel):
    name: str
    tokens_saved: int
    applied: bool


class OptimizeResponse(BaseModel):
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
