from dataclasses import dataclass, field


# Resultado produzido por uma única estratégia de otimização.
@dataclass
class StrategyResult:
    name: str           # identificador interno da estratégia (ex: "stopword_removal")
    original_text: str  # texto recebido por esta estratégia
    optimized_text: str # texto após a aplicação desta estratégia
    tokens_saved: int   # diferença na contagem de tokens (original - otimizado)
    applied: bool = True


# Resultado agregado retornado por Optimizer.optimize().
# Propriedades calculadas de forma lazy a partir dos campos de token/custo armazenados.
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
