from optimizer.nlp import (
    remove_stopwords,
    remove_redundant_phrases,
    collapse_whitespace,
)


def test_remove_stopwords_reduces_text():
    text = "This is a very simple test of the stopword removal function."
    result = remove_stopwords(text)
    assert len(result) < len(text)


def test_remove_stopwords_keeps_negations():
    text = "Do not remove this word."
    result = remove_stopwords(text)
    assert "not" in result


def test_remove_redundant_phrases_deduplicates():
    text = "The sky is blue. The sky is blue. Something else."
    result = remove_redundant_phrases(text)
    assert result.count("sky is blue") == 1


def test_remove_redundant_phrases_keeps_unique():
    text = "First sentence. Second sentence. Third sentence."
    result = remove_redundant_phrases(text)
    assert "First" in result
    assert "Second" in result
    assert "Third" in result


def test_collapse_whitespace():
    text = "Too   many   spaces\n\n\n\nand newlines."
    result = collapse_whitespace(text)
    assert "   " not in result
    assert "\n\n\n" not in result
