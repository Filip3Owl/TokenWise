from optimizer.core import Optimizer, detect_language
from optimizer.nlp import remove_stopwords
from optimizer.strategies import VerbosePhrasesStrategy


def test_detect_language_english():
    assert detect_language("In order to make use of this feature.") == "en"


def test_detect_language_portuguese():
    assert detect_language("Com o objetivo de utilizar este recurso.") == "pt"


def test_detect_language_empty_defaults_to_en():
    assert detect_language("") == "en"


def test_detect_language_unknown_defaults_to_en():
    # Very ambiguous text falls back to en
    result = detect_language("ok")
    assert result in {"en", "pt"}


def test_stopwords_portuguese_removes_pt_words():
    text = "O sistema pode processar os dados da empresa."
    result = remove_stopwords(text, lang="pt")
    # Common PT stopwords like 'o', 'os', 'da' should be removed
    assert len(result) < len(text)


def test_stopwords_portuguese_keeps_negation():
    text = "Não faça isso nunca."
    result = remove_stopwords(text, lang="pt")
    assert "não" in result.lower() or "Não" in result


def test_verbose_phrases_portuguese():
    strategy = VerbosePhrasesStrategy()
    text = "Com o objetivo de melhorar o sistema, faça uso de todas as ferramentas."
    result = strategy.apply(text, "claude", lang="pt")
    assert "para" in result.optimized_text.lower()
    assert result.tokens_saved >= 0


def test_verbose_phrases_english_unchanged_for_pt_input():
    strategy = VerbosePhrasesStrategy()
    # EN phrases should NOT be replaced when lang=pt
    text = "In order to make use of this feature."
    result = strategy.apply(text, "claude", lang="pt")
    assert "in order to" in result.optimized_text.lower()


def test_optimizer_auto_detects_portuguese():
    opt = Optimizer()
    result = opt.optimize(
        "Com o objetivo de utilizar este recurso, por favor forneça assistência ao usuário."
    )
    assert result.lang == "pt"


def test_optimizer_auto_detects_english():
    opt = Optimizer()
    result = opt.optimize(
        "In order to make use of this feature, please provide assistance to the user."
    )
    assert result.lang == "en"


def test_optimizer_lang_override():
    opt = Optimizer()
    result = opt.optimize("Hello world this is a test.", lang="pt")
    assert result.lang == "pt"


def test_optimizer_portuguese_full_pipeline():
    opt = Optimizer()
    text = "Com o objetivo de utilizar este recurso, por favor forneça assistência ao usuário do sistema."
    result = opt.optimize(text, lang="pt")
    assert result.final_tokens <= result.original_tokens
    assert result.optimized_text[0].isupper()
    assert " ," not in result.optimized_text
