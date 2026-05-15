from optimizer.pricing import get_price, calculate_cost, format_cost


def test_get_price_exact_match():
    price = get_price("claude-sonnet-4-6")
    assert price.input_per_million == 3.00


def test_get_price_prefix_claude():
    price = get_price("claude")
    assert price.input_per_million > 0


def test_get_price_prefix_gpt4():
    price = get_price("gpt-4")
    assert price.input_per_million == 30.00


def test_get_price_prefix_gpt4o():
    price = get_price("gpt-4o")
    assert price.input_per_million == 2.50


def test_get_price_unknown_falls_back():
    price = get_price("unknown-model-xyz")
    assert price.input_per_million > 0


def test_calculate_cost_zero_tokens():
    assert calculate_cost(0, "claude") == 0.0


def test_calculate_cost_one_million_tokens():
    cost = calculate_cost(1_000_000, "claude-sonnet-4-6")
    assert cost == 3.00


def test_calculate_cost_proportional():
    cost_500k = calculate_cost(500_000, "claude-sonnet-4-6")
    cost_1m = calculate_cost(1_000_000, "claude-sonnet-4-6")
    assert abs(cost_500k - cost_1m / 2) < 0.0001


def test_format_cost_zero():
    assert format_cost(0) == "$0.00"


def test_format_cost_small():
    result = format_cost(0.000003)
    assert result.startswith("$")
    assert "0.000003" in result


def test_format_cost_normal():
    result = format_cost(1.5)
    assert result == "$1.5000"


def test_optimization_result_cost_fields():
    from optimizer.core import Optimizer
    opt = Optimizer()
    result = opt.optimize(
        "In order to make use of this feature, please be advised.",
        model="claude-sonnet-4-6",
    )
    assert result.original_cost > 0
    assert result.final_cost >= 0
    assert result.cost_saved >= 0
    assert result.cost_savings_pct == result.savings_pct
