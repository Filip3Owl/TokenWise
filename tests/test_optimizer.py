from optimizer.core import Optimizer
from optimizer.models import OptimizationResult
from optimizer.strategies import VerbosePhrasesStrategy, WhitespaceCollapseStrategy


def test_optimizer_returns_result():
    opt = Optimizer()
    result = opt.optimize("Please make use of this feature in order to improve performance.")
    assert isinstance(result, OptimizationResult)


def test_optimizer_reduces_tokens():
    opt = Optimizer()
    text = (
        "In order to make use of this feature, please be advised that you "
        "should provide assistance to the user. Due to the fact that it is "
        "important to note that performance matters, has the ability to scale."
    )
    result = opt.optimize(text)
    assert result.final_tokens <= result.original_tokens


def test_optimizer_conservative_mode():
    opt = Optimizer(conservative=True)
    result = opt.optimize("Hello world, this is a test sentence.")
    assert isinstance(result, OptimizationResult)
    assert len(result.strategy_results) > 0


def test_optimizer_savings_pct():
    opt = Optimizer()
    result = opt.optimize(
        "In order to make use of this. In order to make use of this."
    )
    assert 0.0 <= result.savings_pct <= 100.0


def test_optimizer_empty_string():
    opt = Optimizer()
    result = opt.optimize("")
    assert result.original_tokens == 0
    assert result.final_tokens == 0


def test_verbose_phrases_strategy():
    strategy = VerbosePhrasesStrategy()
    result = strategy.apply("In order to succeed, make use of all tools.", "claude")
    assert "to succeed" in result.optimized_text
    assert "use" in result.optimized_text


def test_whitespace_strategy_saves_tokens():
    strategy = WhitespaceCollapseStrategy()
    text = "Too    many   spaces   here."
    result = strategy.apply(text, "claude")
    assert result.tokens_saved >= 0
    assert "  " not in result.optimized_text
