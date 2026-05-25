import re


def fix_punctuation_spacing(text: str) -> str:
    # Remove espaço antes de sinais de pontuação
    text = re.sub(r'\s+([.,!?;:)\]])', r'\1', text)
    # Remove espaço após colchetes de abertura
    text = re.sub(r'([\[(])\s+', r'\1', text)
    # Garante um único espaço após pontuação quando seguido de uma palavra
    text = re.sub(r'([.,!?;:])\s*([A-Za-z])', r'\1 \2', text)
    return text


def fix_capitalization(text: str) -> str:
    # Capitaliza o primeiro caractere do texto
    text = text.strip()
    if not text:
        return text
    text = text[0].upper() + text[1:]

    # Capitaliza a primeira letra após pontuação de fim de frase
    text = re.sub(r'([.!?])\s+([a-z])', lambda m: m.group(1) + ' ' + m.group(2).upper(), text)
    return text


def fix_multiple_spaces(text: str) -> str:
    return re.sub(r'  +', ' ', text).strip()


def fix_apostrophes(text: str) -> str:
    # Reconecta contrações com apóstrofo separadas pela tokenização: "do n't" → "don't"
    text = re.sub(r"\b(\w+)\s+n't\b", r"\1n't", text)
    text = re.sub(r"\b(\w+)\s+'s\b",  r"\1's",  text)
    text = re.sub(r"\b(\w+)\s+'re\b", r"\1're", text)
    text = re.sub(r"\b(\w+)\s+'ve\b", r"\1've", text)
    text = re.sub(r"\b(\w+)\s+'ll\b", r"\1'll", text)
    text = re.sub(r"\b(\w+)\s+'d\b",  r"\1'd",  text)
    return text


def postprocess(text: str) -> str:
    text = fix_multiple_spaces(text)
    text = fix_apostrophes(text)
    text = fix_punctuation_spacing(text)
    text = fix_capitalization(text)
    text = fix_multiple_spaces(text)
    return text
