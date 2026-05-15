from .models import OptimizationResult, StrategyResult
from .strategies import DEFAULT_STRATEGIES, CONSERVATIVE_STRATEGIES, Strategy
from .tokenizer import count_tokens


class Optimizer:
    def __init__(self, strategies: list[Strategy] | None = None, conservative: bool = False):
        if strategies is not None:
            self.strategies = strategies
        elif conservative:
            self.strategies = CONSERVATIVE_STRATEGIES
        else:
            self.strategies = DEFAULT_STRATEGIES

    def optimize(self, text: str, model: str = "claude") -> OptimizationResult:
        original_tokens = count_tokens(text, model)
        current_text = text
        strategy_results: list[StrategyResult] = []

        for strategy in self.strategies:
            result = strategy.apply(current_text, model)
            strategy_results.append(result)
            if result.tokens_saved > 0:
                current_text = result.optimized_text

        final_tokens = count_tokens(current_text, model)

        return OptimizationResult(
            original_text=text,
            optimized_text=current_text,
            original_tokens=original_tokens,
            final_tokens=final_tokens,
            model=model,
            strategy_results=strategy_results,
        )
