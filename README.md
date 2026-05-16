<p align="center">
  <img src="assets/tokenwise_logo.svg" alt="TokenWise Logo" width="480"/>
</p>

<p align="center">
  <strong>Reduce LLM token consumption without losing prompt meaning.</strong><br/>
  NLP-powered optimizer for Claude, GPT-4, and Codex prompts — English and Portuguese.
</p>

<p align="center">
  <img src="https://img.shields.io/badge/python-3.14-blue?style=flat-square&logo=python&logoColor=white"/>
  <img src="https://img.shields.io/badge/license-MIT-green?style=flat-square"/>
  <img src="https://img.shields.io/badge/models-Claude%20%7C%20GPT--4%20%7C%20Codex-6366f1?style=flat-square"/>
  <img src="https://img.shields.io/badge/languages-EN%20%7C%20PT-green?style=flat-square"/>
  <img src="https://img.shields.io/badge/tests-75%20passing-brightgreen?style=flat-square"/>
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
| `claude-opus-4-7` | $15.00 / 1M tokens |
| `claude-sonnet-4-6` | $3.00 / 1M tokens |
| `claude-haiku-4-5` | $0.80 / 1M tokens |
| `gpt-4o` | $2.50 / 1M tokens |
| `gpt-4` | $30.00 / 1M tokens |
| `gpt-4o-mini` | $0.15 / 1M tokens |
| `gpt-3.5-turbo` | $0.50 / 1M tokens |
| `codex` / `text-davinci` | $2.00 / 1M tokens |

Prefix matching is supported — `claude`, `gpt-4`, `gpt-3.5`, `codex` all resolve automatically.

## Running Tests

```bash
python -m pytest tests/ -v
```

75 tests across tokenizer, NLP, strategies, pricing, postprocessor, language detection, optimizer pipeline, and CLI integration.

## Project Structure

```
TokenWise/
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

### In progress
- `POST /optimize` REST API endpoint (FastAPI) — so any app can optimize prompts via HTTP

### Planned
- `POST /chat` proxy endpoint — TokenWise optimizes the prompt and forwards to Claude/GPT, returning the LLM response
- `--json` flag — machine-readable output for scripting
- `--diff` flag — show exactly what changed between original and optimized
- Spanish (`es`) language support

## License

MIT
