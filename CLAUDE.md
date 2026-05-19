# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Purpose

Python CLI tool and REST API that analyzes and optimizes text prompts to reduce token consumption when calling LLM APIs (Claude, GPT-4, Gemini). Supports English and Portuguese. Uses NLTK for linguistic processing, `tiktoken` for accurate token counting, `langdetect` for automatic language detection, and `rich` for CLI output.

Phases A, B, and C are complete. The REST API (FastAPI) exposes `POST /optimize` and `POST /chat`. The `/chat` endpoint acts as a transparent middleware — it optimizes the prompt and forwards it to Anthropic, OpenAI, or Google Gemini, returning the LLM response alongside savings metadata. Protected by per-client Bearer token auth (SQLite) with per-client rate limiting (basic=60 req/min, pro=300 req/min). Admin endpoints at `/admin/clients` manage client tokens and are protected by the master `TOKENWISE_API_KEY`.

## Environment

```bash
source venv/bin/activate   # activate before running anything
pip install -e .           # install package + dependencies (editable mode)
```

Python 3.14 · key dependencies: `nltk`, `tiktoken`, `langdetect`, `rich`, `fastapi`, `uvicorn`, `httpx`

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
# TOKENWISE_API_KEY  — master admin key for /admin/clients endpoints (generate with secrets.token_urlsafe(32))
# ANTHROPIC_API_KEY  — required for POST /chat with claude-* models
# OPENAI_API_KEY     — required for POST /chat with gpt-* models
# GOOGLE_API_KEY     — required for POST /chat with gemini-* models

# First-time setup: create a client token before calling /optimize or /chat
# curl -X POST http://127.0.0.1:8000/admin/clients \
#   -H "Authorization: Bearer $TOKENWISE_API_KEY" \
#   -H "Content-Type: application/json" \
#   -d '{"name": "my-app", "plan": "basic"}'

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
  main.py              — FastAPI app: health, optimize, chat + admin router; DB init on startup
  admin.py             — /admin/clients CRUD router (Phase C)
  auth.py              — require_admin_auth (env var) + require_client_auth (DB + rate limit)
  database.py          — SQLite client store via stdlib sqlite3: init_db, create/get/list/update/revoke
  config.py            — Central config: MAX_PROMPT_CHARS, LLM_TIMEOUT_SECONDS
  llm.py               — Upstream LLM client: Anthropic + OpenAI + Google Gemini via httpx
  schemas.py           — Pydantic models: OptimizeRequest/Response, ChatRequest/Response, ClientCreate/Update/Response
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
  test_api.py          — API integration tests: /optimize, /chat (mocked LLM + DB), auth, rate limit
  test_admin.py        — Admin endpoint tests: CRUD + rate limit enforcement (Phase C)
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
`POST /chat` — optimizes the prompt and forwards it to Anthropic, OpenAI, or Google Gemini, returning the LLM response + savings metadata.
- Payload cap: 10,000 characters
- LLM timeout: 30 seconds (`httpx`)
- Supports `claude-*`, `gpt-*`, `gemini-*`

### Done: Multi-tenant auth (Phase C) ✓
Per-client API tokens with individual rate limits stored in SQLite (`tokenwise.db`).
- `/admin/clients` CRUD — protected by master `TOKENWISE_API_KEY`
- Plans: `basic` (60 req/min) · `pro` (300 req/min) · fully customizable per client
- Per-client sliding-window rate limiting in `auth.py` (no Redis needed for single-process)
- Tokens are soft-deleted on revocation (`is_active = 0`)

### Planned features
- `--json` CLI flag — machine-readable output
- `--diff` CLI flag — show what changed
- Spanish (`es`) language support
