import re
from abc import ABC, abstractmethod

from .models import StrategyResult
from .tokenizer import count_tokens
from . import nlp


class Strategy(ABC):
    @property
    @abstractmethod
    def name(self) -> str: ...

    @abstractmethod
    def apply(self, text: str, model: str, lang: str = "en") -> StrategyResult: ...


class WhitespaceCollapseStrategy(Strategy):
    name = "whitespace_collapse"

    def apply(self, text: str, model: str, lang: str = "en") -> StrategyResult:
        before = count_tokens(text, model)
        optimized = nlp.collapse_whitespace(text)
        after = count_tokens(optimized, model)
        return StrategyResult(self.name, text, optimized, before - after)


class RedundancyRemovalStrategy(Strategy):
    name = "redundancy_removal"

    def apply(self, text: str, model: str, lang: str = "en") -> StrategyResult:
        before = count_tokens(text, model)
        optimized = nlp.remove_redundant_phrases(text, lang=lang)
        after = count_tokens(optimized, model)
        return StrategyResult(self.name, text, optimized, before - after)


class StopwordRemovalStrategy(Strategy):
    name = "stopword_removal"

    def apply(self, text: str, model: str, lang: str = "en") -> StrategyResult:
        before = count_tokens(text, model)
        optimized = nlp.remove_stopwords(text, lang=lang)
        after = count_tokens(optimized, model)
        return StrategyResult(self.name, text, optimized, before - after)


class LemmatizationStrategy(Strategy):
    name = "lemmatization"

    def apply(self, text: str, model: str, lang: str = "en") -> StrategyResult:
        before = count_tokens(text, model)
        optimized = nlp.lemmatize(text, lang=lang)
        after = count_tokens(optimized, model)
        return StrategyResult(self.name, text, optimized, before - after)


class VerbosePhrasesStrategy(Strategy):
    """Replace common verbose patterns with concise equivalents."""
    name = "verbose_phrases"

    _REPLACEMENTS_EN: list[tuple[str, str]] = [
        (r"\bin order to\b", "to"),
        (r"\bdue to the fact that\b", "because"),
        (r"\bat this point in time\b", "now"),
        (r"\bfor the purpose of\b", "for"),
        (r"\bin the event that\b", "if"),
        (r"\bit is important to note that\b", "note:"),
        (r"\bplease be advised that\b", ""),
        (r"\bas a matter of fact\b", "in fact"),
        (r"\bwith regard to\b", "regarding"),
        (r"\bin spite of the fact that\b", "although"),
        (r"\bmake use of\b", "use"),
        (r"\bprovide assistance to\b", "help"),
        (r"\bhas the ability to\b", "can"),
        (r"\bis able to\b", "can"),
        (r"\bwith the exception of\b", "except"),
        (r"\ba large number of\b", "many"),
        (r"\ba small number of\b", "few"),
        (r"\bon a regular basis\b", "regularly"),
    ]

    _REPLACEMENTS_PT: list[tuple[str, str]] = [
        (r"\bcom o objetivo de\b", "para"),
        (r"\bdevido ao fato de que\b", "porque"),
        (r"\bno momento atual\b", "agora"),
        (r"\bcom a finalidade de\b", "para"),
        (r"\bno caso de que\b", "se"),
        (r"\bé importante observar que\b", "nota:"),
        (r"\bpor favor, note que\b", ""),
        (r"\bfazer uso de\b", "usar"),
        (r"\bprestar assistência a\b", "ajudar"),
        (r"\btem a capacidade de\b", "pode"),
        (r"\bé capaz de\b", "pode"),
        (r"\bà exceção de\b", "exceto"),
        (r"\bum grande número de\b", "muitos"),
        (r"\bum pequeno número de\b", "poucos"),
        (r"\bde forma regular\b", "regularmente"),
        (r"\bno que diz respeito a\b", "sobre"),
        (r"\bapesar do fato de que\b", "embora"),
        (r"\bcom relação a\b", "sobre"),
        (r"\bpor meio de\b", "via"),
        (r"\bpor conta de\b", "por"),
        (r"\bpelo fato de\b", "porque"),
        (r"\bcom base em\b", "baseado em"),
    ]

    def apply(self, text: str, model: str, lang: str = "en") -> StrategyResult:
        before = count_tokens(text, model)
        optimized = text
        replacements = self._REPLACEMENTS_PT if lang == "pt" else self._REPLACEMENTS_EN
        for pattern, replacement in replacements:
            optimized = re.sub(pattern, replacement, optimized, flags=re.IGNORECASE)
        optimized = nlp.collapse_whitespace(optimized)
        after = count_tokens(optimized, model)
        return StrategyResult(self.name, text, optimized, before - after)


DEFAULT_STRATEGIES: list[Strategy] = [
    WhitespaceCollapseStrategy(),
    VerbosePhrasesStrategy(),
    RedundancyRemovalStrategy(),
    StopwordRemovalStrategy(),
    LemmatizationStrategy(),
]

CONSERVATIVE_STRATEGIES: list[Strategy] = [
    WhitespaceCollapseStrategy(),
    VerbosePhrasesStrategy(),
    RedundancyRemovalStrategy(),
]
