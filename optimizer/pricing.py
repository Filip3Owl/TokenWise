from dataclasses import dataclass


@dataclass(frozen=True)
class ModelPrice:
    input_per_million: float   # USD per 1M input tokens
    output_per_million: float  # USD per 1M output tokens


# Prices as of May 2025
_PRICES: dict[str, ModelPrice] = {
    # Claude
    "claude-opus-4-7":          ModelPrice(15.00, 75.00),
    "claude-sonnet-4-6":        ModelPrice(3.00,  15.00),
    "claude-haiku-4-5":         ModelPrice(0.80,   4.00),
    # OpenAI
    "gpt-4o":                   ModelPrice(2.50,  10.00),
    "gpt-4":                    ModelPrice(30.00, 60.00),
    "gpt-4o-mini":              ModelPrice(0.15,   0.60),
    "gpt-3.5-turbo":            ModelPrice(0.50,   1.50),
    # Codex / legacy
    "text-davinci-003":         ModelPrice(2.00,   2.00),
    "code-davinci-002":         ModelPrice(2.00,   2.00),
}

# Prefix fallbacks when no exact match is found
_PREFIX_FALLBACKS: list[tuple[str, str]] = [
    ("claude-opus",   "claude-opus-4-7"),
    ("claude-sonnet", "claude-sonnet-4-6"),
    ("claude-haiku",  "claude-haiku-4-5"),
    ("claude",        "claude-sonnet-4-6"),
    ("gpt-4o-mini",   "gpt-4o-mini"),
    ("gpt-4o",        "gpt-4o"),
    ("gpt-4",         "gpt-4"),
    ("gpt-3.5",       "gpt-3.5-turbo"),
    ("codex",         "text-davinci-003"),
    ("text-davinci",  "text-davinci-003"),
]


def get_price(model: str) -> ModelPrice:
    model_lower = model.lower()
    if model_lower in _PRICES:
        return _PRICES[model_lower]
    for prefix, canonical in _PREFIX_FALLBACKS:
        if model_lower.startswith(prefix):
            return _PRICES[canonical]
    # Default to claude-sonnet when unknown
    return _PRICES["claude-sonnet-4-6"]


def calculate_cost(tokens: int, model: str) -> float:
    """Return USD cost for a given token count (input side)."""
    return (tokens / 1_000_000) * get_price(model).input_per_million


def format_cost(usd: float) -> str:
    if usd == 0:
        return "$0.00"
    if usd < 0.000001:
        return f"${usd:.8f}"
    if usd < 0.01:
        return f"${usd:.6f}"
    return f"${usd:.4f}"
