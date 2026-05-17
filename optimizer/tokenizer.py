import tiktoken

_MODEL_ENCODING: dict[str, str] = {
    "claude": "cl100k_base",
    "gpt-4": "cl100k_base",
    "gpt-3.5": "cl100k_base",
    "codex": "p50k_base",
    "text-davinci": "p50k_base",
    # Gemini uses a different tokenizer internally, but cl100k_base is a close
    # enough approximation for cost estimation purposes
    "gemini": "cl100k_base",
}


def _get_encoding(model: str) -> tiktoken.Encoding:
    model_lower = model.lower()
    for prefix, encoding_name in _MODEL_ENCODING.items():
        if model_lower.startswith(prefix):
            return tiktoken.get_encoding(encoding_name)
    return tiktoken.get_encoding("cl100k_base")


def count_tokens(text: str, model: str = "claude") -> int:
    enc = _get_encoding(model)
    return len(enc.encode(text))


def tokenize(text: str, model: str = "claude") -> list[str]:
    enc = _get_encoding(model)
    token_ids = enc.encode(text)
    return [enc.decode([tid]) for tid in token_ids]
