from dataclasses import dataclass, field


# Result produced by a single optimization strategy.
@dataclass
class StrategyResult:
    name: str           # internal strategy identifier (e.g. "stopword_removal")
    original_text: str  # text received by this strategy
    optimized_text: str # text after this strategy was applied
    tokens_saved: int   # difference in token count (original - optimized)
    applied: bool = True


# Aggregated result returned by Optimizer.optimize().
# Properties are computed lazily from the stored token/cost fields.
@dataclass
class OptimizationResult:
    original_text: str
    optimized_text: str
    original_tokens: int
    final_tokens: int
    model: str
    lang: str = "en"
    original_cost: float = 0.0
    final_cost: float = 0.0
    strategy_results: list[StrategyResult] = field(default_factory=list)

    @property
    def tokens_saved(self) -> int:
        return self.original_tokens - self.final_tokens

    @property
    def savings_pct(self) -> float:
        if self.original_tokens == 0:
            return 0.0
        return (self.tokens_saved / self.original_tokens) * 100

    @property
    def cost_saved(self) -> float:
        return self.original_cost - self.final_cost

    @property
    def cost_savings_pct(self) -> float:
        if self.original_cost == 0:
            return 0.0
        return (self.cost_saved / self.original_cost) * 100
