from dataclasses import dataclass, field


@dataclass
class StrategyResult:
    name: str
    original_text: str
    optimized_text: str
    tokens_saved: int
    applied: bool = True


@dataclass
class OptimizationResult:
    original_text: str
    optimized_text: str
    original_tokens: int
    final_tokens: int
    model: str
    strategy_results: list[StrategyResult] = field(default_factory=list)

    @property
    def tokens_saved(self) -> int:
        return self.original_tokens - self.final_tokens

    @property
    def savings_pct(self) -> float:
        if self.original_tokens == 0:
            return 0.0
        return (self.tokens_saved / self.original_tokens) * 100
