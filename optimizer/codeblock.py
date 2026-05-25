import re

_PLACEHOLDER = "TWCB{}X"  # curto, sem espaços, sobrevive à tokenização do NLTK

# A ordem importa: blocos com cerca devem ser detectados antes do inline
_PATTERNS = [
    r"```[\s\S]*?```",   # blocos com três backticks
    r"`[^`\n]+`",        # código inline com backtick simples
]
_COMBINED = re.compile("|".join(_PATTERNS), re.DOTALL)


def extract(text: str) -> tuple[str, list[str]]:
    """Substitui blocos de código por placeholders. Retorna (texto_modificado, blocos_originais)."""
    blocks: list[str] = []

    def _replace(match: re.Match) -> str:
        idx = len(blocks)
        blocks.append(match.group(0))
        return _PLACEHOLDER.format(idx)

    return _COMBINED.sub(_replace, text), blocks


def restore(text: str, blocks: list[str]) -> str:
    """Restaura os blocos de código originais a partir dos placeholders."""
    for i, block in enumerate(blocks):
        text = text.replace(_PLACEHOLDER.format(i), block)
    return text
