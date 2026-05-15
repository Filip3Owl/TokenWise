from optimizer.tokenizer import count_tokens, tokenize


def test_count_tokens_basic():
    assert count_tokens("Hello world") > 0


def test_count_tokens_empty():
    assert count_tokens("") == 0


def test_count_tokens_longer_text_has_more_tokens():
    short = count_tokens("Hello")
    long = count_tokens("Hello world, this is a longer sentence.")
    assert long > short


def test_count_tokens_model_aware():
    text = "Optimize this prompt for the model."
    claude_count = count_tokens(text, model="claude")
    gpt4_count = count_tokens(text, model="gpt-4")
    # Both use cl100k_base, should be equal
    assert claude_count == gpt4_count


def test_tokenize_returns_list():
    tokens = tokenize("Hello world", model="claude")
    assert isinstance(tokens, list)
    assert len(tokens) > 0


def test_tokenize_unknown_model_fallback():
    count = count_tokens("test text", model="unknown-model-xyz")
    assert count > 0
