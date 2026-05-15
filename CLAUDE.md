# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Purpose

Python CLI tool that analyzes and optimizes text prompts to reduce token consumption when calling LLM APIs (Claude, GPT-4, Codex). Supports English and Portuguese. Uses NLTK for linguistic processing, `tiktoken` for accurate token counting, `langdetect` for automatic language detection, and `rich` for CLI output.

## Environment

```bash
source venv/bin/activate   # activate before running anything
pip install -e .           # install package + dependencies (editable mode)
```

Python 3.14 · key dependencies: `nltk`, `tiktoken`, `langdetect`, `rich`

## Commands

```bash
# Run the optimizer (installed as global command)
tokenwise "Your prompt here"
tokenwise --file prompt.txt --model claude-sonnet-4-6
tokenwise --lang pt "Seu prompt aqui"
tokenwise --conservative "prompt"
tokenwise --no-report "prompt"

# Run tests
python -m pytest tests/ -v
python -m pytest tests/test_optimizer.py::test_name   # single test

# Download NLTK data (first run only — SSL fix required on macOS)
python -c "
import ssl, nltk
ssl._create_default_https_context = ssl._create_unverified_context
nltk.download('punkt_tab'); nltk.download('stopwords')
nltk.download('wordnet'); nltk.download('omw-1.4'); nltk.download('rslp')
"
```

## Architecture

```
main.py                — CLI entry point (argparse + rich), calls Optimizer
optimizer/
  core.py              — Optimizer class: language detection + strategy pipeline
  tokenizer.py         — Token counting via tiktoken (model-aware)
  nlp.py               — NLTK processing: stopwords, lemmatization, redundancy (en + pt)
  strategies.py        — Pluggable Strategy classes; verbose phrase lists for en and pt
  postprocessor.py     — Output quality fix: punctuation spacing, capitalization, apostrophes
  pricing.py           — Per-model USD cost table + calculate_cost() / format_cost()
  models.py            — Dataclasses: OptimizationResult, StrategyResult
tests/
  test_optimizer.py
  test_tokenizer.py
  test_nlp.py
  test_postprocessor.py
  test_pricing.py
  test_lang.py
pyproject.toml         — package entry point: tokenwise = "main:main"
requirements.txt
```

## Optimization Pipeline

Each call to `Optimizer.optimize(text, model, lang)` in `core.py`:
1. **Language detection** — `langdetect` auto-detects `en`/`pt`; overridden by `lang` arg
2. **Strategy chain** — five `Strategy` objects applied in order, each returning `StrategyResult`
3. **Postprocessing** — `postprocessor.postprocess()` fixes punctuation, capitalization, apostrophes
4. **Cost calculation** — `pricing.calculate_cost()` maps token counts to USD per model
5. **Result** — `OptimizationResult` with tokens, costs, savings %, lang, and per-strategy breakdown

### Strategy interface

Every strategy in `strategies.py` implements:
```python
def apply(self, text: str, model: str, lang: str = "en") -> StrategyResult
```

Two presets in `strategies.py`: `DEFAULT_STRATEGIES` (all 5) and `CONSERVATIVE_STRATEGIES` (whitespace + verbose + redundancy only).

### Language support

| Feature | English | Portuguese |
|---|---|---|
| Stopword removal | ✓ 179 effective words | ✓ 207 effective words |
| Verbose phrase replacement | ✓ 18 patterns | ✓ 22 patterns |
| Redundancy removal | ✓ | ✓ |
| Lemmatization | ✓ NLTK WordNet | ✗ (stemmers too aggressive) |

## Model Token Encoding

`tokenizer.py` maps model name prefixes to tiktoken encodings:
- `claude-*`, `gpt-4*`, `gpt-3.5*` → `cl100k_base`
- `codex`, `text-davinci` → `p50k_base`
- Unknown models fall back to `cl100k_base`

Token counts are always model-specific; never use character-based estimates.

## Pricing

`pricing.py` holds a static price table (USD per 1M input tokens). Prefix matching resolves short names like `claude` → `claude-sonnet-4-6`. Unknown models fall back to `claude-sonnet-4-6` pricing. Update `_PRICES` when model prices change.
