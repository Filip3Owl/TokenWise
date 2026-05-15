import ssl
import re

# macOS SSL fix for NLTK downloads
ssl._create_default_https_context = ssl._create_unverified_context

import nltk
from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer
from nltk.tokenize import sent_tokenize, word_tokenize

_STOP_WORDS = set(stopwords.words("english"))
_LEMMATIZER = WordNetLemmatizer()

# Words that look like stopwords but carry semantic weight in prompts
_KEEP_WORDS = {
    "not", "no", "never", "only", "just", "very", "must", "should",
    "need", "please", "do", "don't", "always", "all", "any", "more",
}
_EFFECTIVE_STOPWORDS = _STOP_WORDS - _KEEP_WORDS


def remove_stopwords(text: str) -> str:
    sentences = sent_tokenize(text)
    result = []
    for sentence in sentences:
        words = word_tokenize(sentence)
        filtered = [w for w in words if w.lower() not in _EFFECTIVE_STOPWORDS or not w.isalpha()]
        result.append(" ".join(filtered))
    return " ".join(result)


def lemmatize(text: str) -> str:
    words = word_tokenize(text)
    lemmatized = [_LEMMATIZER.lemmatize(w) if w.isalpha() else w for w in words]
    return " ".join(lemmatized)


def remove_redundant_phrases(text: str) -> str:
    """Remove duplicate sentences and near-duplicate clause fragments."""
    sentences = sent_tokenize(text)
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
