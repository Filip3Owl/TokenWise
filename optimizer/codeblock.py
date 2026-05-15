import re

_PLACEHOLDER = "TWCB{}X"  # short, no spaces, survives NLTK tokenization

# Order matters: fenced blocks must be matched before inline
_PATTERNS = [
    r"```[\s\S]*?```",   # fenced triple-backtick blocks
    r"`[^`\n]+`",        # inline single-backtick code
]
_COMBINED = re.compile("|".join(_PATTERNS), re.DOTALL)


def extract(text: str) -> tuple[str, list[str]]:
    """Replace code blocks with placeholders. Returns (modified_text, original_blocks)."""
    blocks: list[str] = []

    def _replace(match: re.Match) -> str:
        idx = len(blocks)
        blocks.append(match.group(0))
        return _PLACEHOLDER.format(idx)

    return _COMBINED.sub(_replace, text), blocks


def restore(text: str, blocks: list[str]) -> str:
    """Restore original code blocks from placeholders."""
    for i, block in enumerate(blocks):
        text = text.replace(_PLACEHOLDER.format(i), block)
    return text
