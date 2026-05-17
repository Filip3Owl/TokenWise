# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Purpose

Python CLI tool and REST API that analyzes and optimizes text prompts to reduce token consumption when calling LLM APIs (Claude, GPT-4, Gemini). Supports English and Portuguese. Uses NLTK for linguistic processing, `tiktoken` for accurate token counting, `langdetect` for automatic language detection, and `rich` for CLI output.

Phases A and B are complete. The REST API (FastAPI) exposes `POST /optimize` and `POST /chat`. The `/chat` endpoint acts as a transparent middleware — it optimizes the prompt and forwards it to Anthropic, OpenAI, or Google Gemini, returning the LLM response alongside savings metadata. Protected by Bearer token auth and rate limiting (60 req/min per IP).

## Environment

```bash
source venv/bin/activate   # activate before running anything
pip install -e .           # install package + dependencies (editable mode)
```

Python 3.14 · key dependencies: `nltk`, `tiktoken`, `langdetect`, `rich`, `fastapi`, `uvicorn`, `slowapi`, `httpx`

## Commands

```bash
# Run the optimizer (installed as global command)
tokenwise "Your prompt here"
tokenwise --file prompt.txt --model claude-sonnet-4-6
tokenwise --lang pt "Seu prompt aqui"
tokenwise --conservative "prompt"
tokenwise --no-report "prompt"
echo "prompt" | tokenwise            # stdin pipe

# Run the REST API
uvicorn api.main:app --reload          # http://127.0.0.1:8000
# Swagger UI: http://127.0.0.1:8000/docs

# Required environment variables (copy .env.example to .env and fill in)
# TOKENWISE_API_KEY  — Bearer token that clients must send (generate with secrets.token_urlsafe(32))
# ANTHROPIC_API_KEY  — required for POST /chat with claude-* models
# OPENAI_API_KEY     — required for POST /chat with gpt-* models
# GOOGLE_API_KEY     — required for POST /chat with gemini-* models

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
api/
  main.py              — FastAPI app: GET /health, POST /optimize, POST /chat
  auth.py              — Bearer token authentication dependency
  config.py            — Central config: MAX_PROMPT_CHARS, LLM_TIMEOUT_SECONDS
  llm.py               — Upstream LLM client: Anthropic + OpenAI + Google Gemini via httpx
  schemas.py           — Pydantic models: OptimizeRequest/Response, ChatRequest/Response
optimizer/
  core.py              — Optimizer class: language detection + strategy pipeline
  tokenizer.py         — Token counting via tiktoken (model-aware)
  nlp.py               — NLTK processing: stopwords, redundancy (en + pt)
  strategies.py        — Pluggable Strategy classes; verbose phrase lists for en and pt
  postprocessor.py     — Output quality fix: punctuation spacing, capitalization, apostrophes
  pricing.py           — Per-model USD cost table + calculate_cost() / format_cost()
  models.py            — Dataclasses: OptimizationResult, StrategyResult
  codeblock.py         — Extract/restore code blocks so they are never modified
tests/
  test_optimizer.py
  test_tokenizer.py
  test_nlp.py
  test_postprocessor.py
  test_pricing.py
  test_lang.py
  test_codeblock.py
  test_cli.py          — CLI integration tests (--conservative, --output, --file, stdin)
  test_api.py          — API integration tests: /optimize, /chat (mocked LLM), auth, rate limit
pyproject.toml         — package entry point: tokenwise = "main:main"
requirements.txt
```

## Optimization Pipeline

Each call to `Optimizer.optimize(text, model, lang)` in `core.py`:
1. **Language detection** — `langdetect` auto-detects `en`/`pt`; overridden by `lang` arg
2. **Code block extraction** — `codeblock.extract()` removes code blocks before optimization
3. **Strategy chain** — four `Strategy` objects applied in order, each returning `StrategyResult`
4. **Postprocessing** — `postprocessor.postprocess()` fixes punctuation, capitalization, apostrophes
5. **Code block restore** — `codeblock.restore()` puts code blocks back untouched
6. **Cost calculation** — `pricing.calculate_cost()` maps token counts to USD per model
7. **Result** — `OptimizationResult` with tokens, costs, savings %, lang, and per-strategy breakdown

### Strategy interface

Every strategy in `strategies.py` implements:
```python
def apply(self, text: str, model: str, lang: str = "en") -> StrategyResult
```

Two presets in `strategies.py`: `DEFAULT_STRATEGIES` (all 4) and `CONSERVATIVE_STRATEGIES` (whitespace + verbose + redundancy only).

### Language support

| Feature | English | Portuguese |
|---|---|---|
| Stopword removal | ✓ 179 effective words | ✓ 207 effective words |
| Verbose phrase replacement | ✓ 18 patterns | ✓ 22 patterns |
| Redundancy removal | ✓ | ✓ |

## Model Token Encoding

`tokenizer.py` maps model name prefixes to tiktoken encodings:
- `claude-*`, `gpt-4*`, `gpt-3.5*` → `cl100k_base`
- `codex`, `text-davinci` → `p50k_base`
- Unknown models fall back to `cl100k_base`

Token counts are always model-specific; never use character-based estimates.

## Pricing

`pricing.py` holds a static price table (USD per 1M input tokens). Prefix matching resolves short names like `claude` → `claude-sonnet-4-6`. Unknown models fall back to `claude-sonnet-4-6` pricing. Update `_PRICES` when model prices change.

## Roadmap

### Done: REST API (Phase A) ✓
`POST /optimize` — optimizes a prompt and returns token/cost savings. No LLM call.

### Done: Proxy endpoint (Phase B) ✓
`POST /chat` — optimizes the prompt and forwards it to Anthropic or OpenAI, returning the LLM response + savings metadata.
- Bearer token auth (`TOKENWISE_API_KEY`)
- Rate limiting: 60 req/min per IP (`slowapi`)
- Payload cap: 10,000 characters
- LLM timeout: 30 seconds (`httpx`)
- Supports `claude-*` (Anthropic) and `gpt-*` (OpenAI)

### Next: Multi-tenant auth (Phase C)
Per-client API tokens with individual rate limits stored in a database. Enables different plans (basic/pro) and per-client revocation.

### Other planned features
- `--json` CLI flag — machine-readable output
- `--diff` CLI flag — show what changed
- Spanish (`es`) language support
