import ssl
import re

# Correção de SSL no macOS para downloads do NLTK
ssl._create_default_https_context = ssl._create_unverified_context

from nltk.corpus import stopwords
from nltk.tokenize import sent_tokenize, word_tokenize

# Palavras que parecem stopwords mas carregam peso semântico em prompts
_KEEP_EN = {
    "not", "no", "never", "only", "just", "very", "must", "should",
    "need", "please", "do", "don't", "always", "all", "any", "more",
}
_KEEP_PT = {
    "não", "nunca", "jamais", "só", "apenas", "muito", "deve", "precisa",
    "por favor", "sempre", "todo", "toda", "qualquer", "mais", "menos",
}
_KEEP_ES = {
    "no", "nunca", "jamás", "solo", "muy", "debe", "necesita",
    "por favor", "siempre", "todo", "toda", "cualquier", "más", "menos",
}

# Expressões de múltiplas palavras que devem ser mantidas intactas mesmo que cada palavra seja uma stopword
_PROTECT_BIGRAMS_PT: set[tuple[str, str]] = {
    ("por", "que"),   # por que
    ("por", "isso"),  # portanto
    ("por", "fim"),   # por fim
    ("o", "que"),     # o que
    ("ao", "invés"),  # ao invés de
}
_PROTECT_BIGRAMS_ES: set[tuple[str, str]] = {
    ("por", "qué"),     # por qué
    ("por", "eso"),     # por eso
    ("por", "favor"),   # por favor
    ("lo", "que"),      # lo que
    ("al", "menos"),    # al menos
    ("sin", "embargo"), # sin embargo
}

_PROTECT_BIGRAMS: dict[str, set[tuple[str, str]]] = {
    "pt": _PROTECT_BIGRAMS_PT,
    "es": _PROTECT_BIGRAMS_ES,
}

_STOPWORDS_EN = stopwords.words("english")
_STOPWORDS_PT = stopwords.words("portuguese")
_STOPWORDS_ES = stopwords.words("spanish")

_EFFECTIVE_STOPWORDS: dict[str, set[str]] = {
    "en": set(_STOPWORDS_EN) - _KEEP_EN,
    "pt": set(_STOPWORDS_PT) - _KEEP_PT,
    "es": set(_STOPWORDS_ES) - _KEEP_ES,
}

_NLTK_LANG: dict[str, str] = {
    "en": "english",
    "pt": "portuguese",
    "es": "spanish",
}


def remove_stopwords(text: str, lang: str = "en") -> str:
    nltk_lang = _NLTK_LANG.get(lang, "english")
    effective = _EFFECTIVE_STOPWORDS.get(lang, _EFFECTIVE_STOPWORDS["en"])
    protect_bigrams = _PROTECT_BIGRAMS.get(lang, set())
    sentences = sent_tokenize(text, language=nltk_lang)
    result = []
    for sentence in sentences:
        words = word_tokenize(sentence, language=nltk_lang)
        filtered = []
        i = 0
        while i < len(words):
            w = words[i]
            if i + 1 < len(words) and (w.lower(), words[i + 1].lower()) in protect_bigrams:
                filtered.append(w)
                filtered.append(words[i + 1])
                i += 2
                continue
            if w.lower() not in effective or not w.isalpha():
                filtered.append(w)
            i += 1
        result.append(" ".join(filtered))
    return " ".join(result)


def remove_redundant_phrases(text: str, lang: str = "en") -> str:
    nltk_lang = _NLTK_LANG.get(lang, "english")
    sentences = sent_tokenize(text, language=nltk_lang)
    seen: set[str] = set()
    unique = []
    for s in sentences:
        normalized = re.sub(r"\s+", " ", s.strip().lower())
        if normalized not in seen:
            seen.add(normalized)
            unique.append(s)
    return " ".join(unique)


def collapse_whitespace(text: str) -> str:
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = re.sub(r"[ \t]+", " ", text)
    return text.strip()
