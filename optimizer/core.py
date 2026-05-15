from langdetect import detect, LangDetectException

from .models import OptimizationResult, StrategyResult
from .strategies import DEFAULT_STRATEGIES, CONSERVATIVE_STRATEGIES, Strategy
from .tokenizer import count_tokens
from .pricing import calculate_cost
from .postprocessor import postprocess
from .codeblock import extract as extract_code, restore as restore_code

_SUPPORTED_LANGS = {"en", "pt"}


def detect_language(text: str) -> str:
    if not text.strip():
        return "en"
    try:
        lang = detect(text)
        return lang if lang in _SUPPORTED_LANGS else "en"
    except LangDetectException:
        return "en"


class Optimizer:
    def __init__(self, strategies: list[Strategy] | None = None, conservative: bool = False):
        if strategies is not None:
            self.strategies = strategies
        elif conservative:
            self.strategies = CONSERVATIVE_STRATEGIES
        else:
            self.strategies = DEFAULT_STRATEGIES

    def optimize(self, text: str, model: str = "claude", lang: str = "auto") -> OptimizationResult:
        resolved_lang = detect_language(text) if lang == "auto" else lang
        original_tokens = count_tokens(text, model)

        current_text, code_blocks = extract_code(text)
        strategy_results: list[StrategyResult] = []

        for strategy in self.strategies:
            result = strategy.apply(current_text, model, lang=resolved_lang)
            strategy_results.append(result)
            if result.tokens_saved > 0:
                current_text = result.optimized_text

        current_text = postprocess(current_text)
        current_text = restore_code(current_text, code_blocks)
        final_tokens = count_tokens(current_text, model)

        return OptimizationResult(
            original_text=text,
            optimized_text=current_text,
            original_tokens=original_tokens,
            final_tokens=final_tokens,
            model=model,
            original_cost=calculate_cost(original_tokens, model),
            final_cost=calculate_cost(final_tokens, model),
            strategy_results=strategy_results,
            lang=resolved_lang,
        )
