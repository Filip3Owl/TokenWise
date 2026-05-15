<p align="center">
  <img src="assets/tokenwise_logo.svg" alt="TokenWise Logo" width="480"/>
</p>

<p align="center">
  <strong>Reduce LLM token consumption without losing prompt meaning.</strong><br/>
  NLP-powered optimizer for Claude, GPT-4, and Codex prompts.
</p>

<p align="center">
  <img src="https://img.shields.io/badge/python-3.14-blue?style=flat-square&logo=python&logoColor=white"/>
  <img src="https://img.shields.io/badge/license-MIT-green?style=flat-square"/>
  <img src="https://img.shields.io/badge/models-Claude%20%7C%20GPT--4%20%7C%20Codex-6366f1?style=flat-square"/>
  <img src="https://img.shields.io/badge/NLTK-powered-orange?style=flat-square"/>
</p>

---

## What it does

TokenWise analyzes your prompts using NLP techniques and applies a chain of optimization strategies to reduce token count — lowering API costs while preserving intent.

```
Original  →  48 tokens
Optimized →  17 tokens   (64.6% saved)
```

## Strategies

| Strategy | Description |
|---|---|
| `whitespace_collapse` | Removes redundant spaces and blank lines |
| `verbose_phrases` | Replaces wordy expressions (`in order to` → `to`) |
| `redundancy_removal` | Eliminates duplicate sentences |
| `stopword_removal` | Drops low-value function words (NLTK) |
| `lemmatization` | Normalizes inflected word forms (NLTK WordNet) |

Two built-in presets: **default** (all strategies) and **conservative** (safe strategies only, preserves natural language).

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
# Optimize a prompt directly
tokenwise "In order to make use of this feature, please be advised that you should provide assistance to the user."

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
```

### Example output

```
╭──────────────────────────── Token Optimizer Report ────────────────────────────╮
│ Model: claude   Original: 21 tokens   Optimized: 7 tokens   Saved: 14 (66.7%) │
╰─────────────────────────────────────────────────────────────────────────────────╯

  Strategy              Tokens saved    Status
 ────────────────────────────────────────────────
  whitespace_collapse              0   no change
  verbose_phrases                 10   applied
  redundancy_removal               0   no change
  stopword_removal                 4   applied
  lemmatization                    0   no change

──────────────────────────── Optimized Prompt ──────────────────────────────
use feature , should help user .
────────────────────────────────────────────────────────────────────────────
```

## Supported Models

| Model | Token Encoding |
|---|---|
| `claude` (all versions) | `cl100k_base` |
| `gpt-4` | `cl100k_base` |
| `gpt-3.5` | `cl100k_base` |
| `codex` / `text-davinci` | `p50k_base` |

## Running Tests

```bash
python -m pytest tests/ -v
```

## Project Structure

```
TokenWise/
├── optimizer/
│   ├── core.py         # Optimizer pipeline
│   ├── strategies.py   # Pluggable optimization strategies
│   ├── nlp.py          # NLTK processing
│   ├── tokenizer.py    # Token counting (tiktoken)
│   └── models.py       # Data types
├── tests/
├── assets/
│   └── tokenwise_logo.svg
├── main.py
├── pyproject.toml
└── requirements.txt
```

## License

MIT
