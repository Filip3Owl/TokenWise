# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Purpose

Python CLI tool that analyzes and optimizes text prompts to reduce token consumption when calling LLM APIs (Claude, OpenAI Codex). Uses NLTK for linguistic processing and `tiktoken` for accurate token counting.

## Environment

```bash
source venv/bin/activate          # activate before running anything
pip install -r requirements.txt   # install/sync dependencies
```

Python 3.14 · dependencies: `nltk`, `tiktoken`, `anthropic`, `openai`, `rich`

## Commands

```bash
# Run the optimizer
python main.py "Your prompt here"
python main.py --file prompt.txt --model claude-sonnet-4-6

# Run tests
python -m pytest tests/
python -m pytest tests/test_optimizer.py::test_name   # single test

# Download NLTK data (first run)
python -c "import nltk; nltk.download('punkt'); nltk.download('stopwords'); nltk.download('wordnet')"
```

## Architecture

```
main.py              — CLI entry point (argparse), calls Optimizer pipeline
optimizer/
  core.py            — Optimizer class: orchestrates the pipeline
  tokenizer.py       — Token counting via tiktoken (model-aware)
  nlp.py             — NLTK-based text processing (stopword removal, lemmatization, redundancy detection)
  strategies.py      — Individual optimization strategies (each returns modified text + savings report)
  models.py          — Dataclasses: OptimizationResult, TokenReport, Strategy
tests/
  test_optimizer.py
  test_tokenizer.py
  test_nlp.py
requirements.txt
```

## Optimization Pipeline

Each prompt runs through a strategy chain in `core.py`:
1. **Tokenize** — count original tokens per target model
2. **NLP preprocessing** — remove stopwords, lemmatize, detect repetition (NLTK)
3. **Strategy application** — each `Strategy` is applied in order; strategies are composable and individually togglable
4. **Report** — `OptimizationResult` carries original count, final count, % savings, and per-strategy breakdown

Strategies live in `strategies.py` and must implement `apply(text: str) -> tuple[str, int]` returning the modified text and tokens saved.

## Model Token Encoding

`tokenizer.py` maps model names to tiktoken encodings:
- `claude-*` → `cl100k_base`
- `gpt-4` / `codex` → `cl100k_base`
- `gpt-3.5` → `cl100k_base`

Token counts are always model-specific; never use character-based estimates.
