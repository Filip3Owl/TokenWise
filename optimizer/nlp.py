import ssl
import re

# macOS SSL fix for NLTK downloads
ssl._create_default_https_context = ssl._create_unverified_context

from nltk.corpus import stopwords
from nltk.tokenize import sent_tokenize, word_tokenize

# Words that look like stopwords but carry semantic weight in prompts
_KEEP_EN = {
    "not", "no", "never", "only", "just", "very", "must", "should",
    "need", "please", "do", "don't", "always", "all", "any", "more",
}
_KEEP_PT = {
    "não", "nunca", "jamais", "só", "apenas", "muito", "deve", "precisa",
    "por favor", "sempre", "todo", "toda", "qualquer", "mais", "menos",
}

_STOPWORDS_EN = stopwords.words("english")
_STOPWORDS_PT = stopwords.words("portuguese")

_EFFECTIVE_STOPWORDS: dict[str, set[str]] = {
    "en": set(_STOPWORDS_EN) - _KEEP_EN,
    "pt": set(_STOPWORDS_PT) - _KEEP_PT,
}

_NLTK_LANG: dict[str, str] = {
    "en": "english",
    "pt": "portuguese",
}


def remove_stopwords(text: str, lang: str = "en") -> str:
    nltk_lang = _NLTK_LANG.get(lang, "english")
    effective = _EFFECTIVE_STOPWORDS.get(lang, _EFFECTIVE_STOPWORDS["en"])
    sentences = sent_tokenize(text, language=nltk_lang)
    result = []
    for sentence in sentences:
        words = word_tokenize(sentence, language=nltk_lang)
        filtered = [w for w in words if w.lower() not in effective or not w.isalpha()]
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
