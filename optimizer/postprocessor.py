import re


def fix_punctuation_spacing(text: str) -> str:
    # Remove space before punctuation marks
    text = re.sub(r'\s+([.,!?;:)\]])', r'\1', text)
    # Remove space after opening brackets
    text = re.sub(r'([\[(])\s+', r'\1', text)
    # Ensure single space after punctuation when followed by a word
    text = re.sub(r'([.,!?;:])\s*([A-Za-z])', r'\1 \2', text)
    return text


def fix_capitalization(text: str) -> str:
    # Capitalize the first character of the whole text
    text = text.strip()
    if not text:
        return text
    text = text[0].upper() + text[1:]

    # Capitalize first letter after sentence-ending punctuation
    text = re.sub(r'([.!?])\s+([a-z])', lambda m: m.group(1) + ' ' + m.group(2).upper(), text)
    return text


def fix_multiple_spaces(text: str) -> str:
    return re.sub(r'  +', ' ', text).strip()


def fix_apostrophes(text: str) -> str:
    # Re-attach apostrophe contractions split by tokenization: "do n't" → "don't"
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
