<p align="center">
  <img src="assets/tokenwise_logo.svg" alt="TokenWise Logo" width="480"/>
</p>

<p align="center">
  <strong>Reduce LLM token consumption without losing prompt meaning.</strong><br/>
  NLP-powered optimizer for Claude, GPT-4, and Gemini prompts — English and Portuguese.
</p>

<p align="center">
  <img src="https://img.shields.io/badge/python-3.14-blue?style=flat-square&logo=python&logoColor=white"/>
  <img src="https://img.shields.io/badge/license-MIT-green?style=flat-square"/>
  <img src="https://img.shields.io/badge/models-Claude%20%7C%20GPT--4%20%7C%20Gemini-6366f1?style=flat-square"/>
  <img src="https://img.shields.io/badge/languages-EN%20%7C%20PT-green?style=flat-square"/>
  <img src="https://img.shields.io/badge/tests-111%20passing-brightgreen?style=flat-square"/>
</p>

---

## What it does

TokenWise analyzes your prompts using NLP techniques and applies a chain of optimization strategies to reduce token count — lowering API costs while preserving intent. Language is detected automatically.

```
Original  →  21 tokens   $0.000063
Optimized →   7 tokens   $0.000021   (66.7% saved)
```

## Pipeline

Each prompt runs through five strategies in sequence, followed by a post-processor that restores correct punctuation, capitalization, and contractions.

| Step | Strategy | Description |
|---|---|---|
| 1 | `whitespace_collapse` | Removes redundant spaces and blank lines |
| 2 | `verbose_phrases` | Replaces wordy expressions — patterns for EN and PT |
| 3 | `redundancy_removal` | Eliminates duplicate sentences |
| 4 | `stopword_removal` | Drops low-value function words (NLTK) |
| ✦ | `postprocessor` | Fixes punctuation spacing, capitalization, and apostrophes |

Two built-in presets: **default** (all strategies) and **conservative** (whitespace + verbose phrases + redundancy only).

## Language Support

Language is detected automatically via `langdetect`. Use `--lang` to override.

| Feature | English | Portuguese |
|---|---|---|
| Stopword removal | ✓ 179 words | ✓ 207 words |
| Verbose phrase replacement | ✓ 18 patterns | ✓ 22 patterns |
| Redundancy removal | ✓ | ✓ |

## Installation

```bash
git clone https://github.com/Filip3Owl/TokenWise.git
cd TokenWise
python3 -m venv venv
source venv/bin/activate
pip install -e .
```

This installs `tokenwise` as a global command — no need to call `python main.py` directly.

> **macOS note:** NLTK data is downloaded automatically on first run.

## Usage

```bash
# Optimize a prompt (language auto-detected)
tokenwise "In order to make use of this feature, please be advised that you should provide assistance to the user."

# Force a language
tokenwise --lang pt "Com o objetivo de utilizar este recurso."
tokenwise --lang en "Your prompt here."

# Read from file
tokenwise --file prompt.txt

# Target a specific model
tokenwise --model gpt-4 "your prompt here"

# Conservative mode (no stopword or lemmatization removal)
tokenwise --conservative "your prompt here"

# Save optimized output to file
tokenwise --file prompt.txt --output optimized.txt

# Print only the result, no report
tokenwise --no-report "your prompt here"

# Pipe text via stdin
echo "your prompt here" | tokenwise
cat prompt.txt | tokenwise
```

## Example output

```
╭────────────────────────────── TokenWise Report ──────────────────────────────╮
│                                                                              │
│  Model     claude   Language  English   Price     $3.00/M tokens             │
│                                                                              │
│  Tokens   41 → 20       Cost     $0.000123 → $0.000060                       │
│  Saved    21 (51.2%)    Saved    $0.000063 (51.2%)                           │
│                                                                              │
╰──────────────────────────────────────────────────────────────────────────────╯
 Strategy                 Savings            Tokens     Status
─────────────────────────────────────────────────────────────────
 Whitespace Collapse      ░░░░░░░░░░░░░░░░        —   no change
 Verbose Phrases          ███████████████░      -10    applied
 Redundancy Removal       ░░░░░░░░░░░░░░░░        —   no change
 Stopword Removal         ████████████████      -11    applied
╭────────────────────────────── Optimized Prompt ──────────────────────────────╮
│                                                                              │
│  Achieve best results, use all available resources help team members         │
│  unable complete tasks lack necessary experience.                            │
│                                                                              │
╰──────────────────────────────────────────────────────────────────────────────╯
```

## Supported Models

| Model | Input price |
|---|---|
**Anthropic**

| Model | Input price |
|---|---|
| `claude-opus-4-7` | $15.00 / 1M tokens |
| `claude-sonnet-4-6` | $3.00 / 1M tokens |
| `claude-haiku-4-5` | $0.80 / 1M tokens |

**OpenAI**

| Model | Input price |
|---|---|
| `gpt-4o` | $2.50 / 1M tokens |
| `gpt-4` | $30.00 / 1M tokens |
| `gpt-4o-mini` | $0.15 / 1M tokens |
| `gpt-3.5-turbo` | $0.50 / 1M tokens |
| `codex` / `text-davinci` | $2.00 / 1M tokens |

**Google Gemini**

| Model | Input price |
|---|---|
| `gemini-3-flash-preview` | $0.50 / 1M tokens |
| `gemini-2.0-flash` | $0.10 / 1M tokens |
| `gemini-1.5-flash` | $0.075 / 1M tokens |
| `gemini-1.5-pro` | $1.25 / 1M tokens |

Prefix matching is supported — `claude`, `gpt-4`, `gemini-3`, `gemini` all resolve automatically.

## REST API

TokenWise exposes a FastAPI server so any app can optimize prompts — or use it as a transparent LLM proxy — over HTTP.

```bash
# Copy and fill in your keys
cp .env.example .env

# Start the server
uvicorn api.main:app --reload
```

Interactive docs available at `http://127.0.0.1:8000/docs`.

### Authentication model

TokenWise uses a two-tier auth system:

| Token type | Used for | Configured via |
|---|---|---|
| **Master key** (`TOKENWISE_API_KEY`) | `/admin/*` endpoints only | env var |
| **Client token** | `/optimize` and `/chat` | created via `POST /admin/clients` |

Start by creating a client token with the master key, then use that client token for API calls.

```bash
# Step 1 — create a client (run once)
curl -X POST http://127.0.0.1:8000/admin/clients \
  -H "Authorization: Bearer $TOKENWISE_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"name": "my-app", "plan": "basic"}'
# → returns a token field — save it

# Step 2 — use the client token for all API calls
Authorization: Bearer <client-token>
```

---

**`POST /admin/clients`** — create a new client token.

```bash
curl -X POST http://127.0.0.1:8000/admin/clients \
  -H "Authorization: Bearer $TOKENWISE_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"name": "my-app", "plan": "pro"}'
```

```json
{
  "id": 1,
  "name": "my-app",
  "token": "abc123...",
  "plan": "pro",
  "rate_limit": 300,
  "is_active": true,
  "created_at": "2026-05-18 10:00:00"
}
```

**`GET /admin/clients`** — list all clients.

**`PATCH /admin/clients/{token}`** — update plan or rate limit.

**`DELETE /admin/clients/{token}`** — revoke a client token.

---

**`POST /optimize`** — optimize a prompt without calling any LLM.

```bash
curl -X POST http://127.0.0.1:8000/optimize \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"text": "In order to be able to help you, I need more information."}'
```

```json
{
  "optimized_text": "Help you, need more information.",
  "original_tokens": 16,
  "final_tokens": 7,
  "tokens_saved": 9,
  "savings_pct": 56.25,
  "original_cost": 0.000048,
  "final_cost": 0.000021,
  "cost_saved": 0.000027,
  "cost_savings_pct": 56.25,
  "model": "claude-sonnet-4-6",
  "lang": "en",
  "strategies": [...]
}
```

---

**`POST /chat`** — optimize and forward to the upstream LLM, returning its response.

```bash
curl -X POST http://127.0.0.1:8000/chat \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"text": "In order to be able to help you, I need more information.", "model": "claude-sonnet-4-6"}'
```

```json
{
  "llm_response": "Of course! Could you tell me a bit more about what you need?",
  "original_tokens": 16,
  "final_tokens": 7,
  "tokens_saved": 9,
  "savings_pct": 56.25,
  "model": "claude-sonnet-4-6",
  "lang": "en"
}
```

Supported models: `claude-*` (requires `ANTHROPIC_API_KEY`) · `gpt-*` (requires `OPENAI_API_KEY`) · `gemini-*` (requires `GOOGLE_API_KEY`)

---

**`GET /health`** — returns `{"status": "ok"}`.

### Request fields

| Field | Description |
|---|---|
| `text` | Prompt to optimize — max 10,000 characters (required) |
| `model` | Target model (default: `claude-sonnet-4-6`) |
| `lang` | `"auto"`, `"en"`, or `"pt"` (default: `"auto"`) |
| `conservative` | Skip stopword removal (default: `false`) |

### Plans and rate limits

| Plan | Rate limit | Set via |
|---|---|---|
| `basic` (default) | 60 req / min | `"plan": "basic"` |
| `pro` | 300 req / min | `"plan": "pro"` |
| Custom | any value 1–10,000 | `"rate_limit": <n>` |

Rate limits are enforced per client token (sliding window), not per IP.

### Security

| Protection | Detail |
|---|---|
| Admin auth | Master `TOKENWISE_API_KEY` env var |
| Client auth | Per-client Bearer token stored in SQLite |
| Rate limiting | Per-client sliding window (plan-based or custom) |
| Payload cap | 10,000 characters max |
| LLM timeout | 30 seconds |

## Running Tests

```bash
python -m pytest tests/ -v
```

111 tests across tokenizer, NLP, strategies, pricing, postprocessor, language detection, optimizer pipeline, CLI integration, REST API (auth, rate limiting, payload limit, `/optimize`, `/chat` with mocked LLM), and admin endpoints.

## Project Structure

```
TokenWise/
├── api/
│   ├── main.py            # FastAPI app: health, optimize, chat + admin router
│   ├── admin.py           # /admin/clients CRUD (Phase C)
│   ├── auth.py            # require_admin_auth + require_client_auth + rate limiting
│   ├── database.py        # SQLite client store (stdlib sqlite3)
│   ├── config.py          # Central config: payload limit, LLM timeout
│   ├── llm.py             # Upstream LLM client (Anthropic + OpenAI + Gemini)
│   └── schemas.py         # Pydantic request/response models
├── optimizer/
│   ├── core.py            # Optimizer pipeline + language detection
│   ├── strategies.py      # Pluggable strategies with EN/PT phrase lists
│   ├── nlp.py             # NLTK processing (en + pt)
│   ├── tokenizer.py       # Token counting (tiktoken)
│   ├── pricing.py         # Per-model USD cost calculation
│   ├── postprocessor.py   # Output quality fix (punctuation, capitalization)
│   └── models.py          # Data types
├── tests/
├── assets/
│   └── tokenwise_logo.svg
├── main.py
├── pyproject.toml
└── requirements.txt
```

## Roadmap

### Done
- `POST /optimize` REST API endpoint (FastAPI) ✓
- `POST /chat` proxy endpoint — optimizes and forwards to Claude / GPT / Gemini ✓
- Per-client API tokens with individual rate limits (Phase C) ✓
  - SQLite client store, `/admin/clients` CRUD
  - Plans: `basic` (60 req/min) and `pro` (300 req/min), fully customizable
  - Sliding-window rate limiting per client token

### Planned
- `--json` flag — machine-readable output for scripting
- `--diff` flag — show exactly what changed between original and optimized
- Spanish (`es`) language support

## License

MIT
