<p align="center">
  <strong>Reduza o consumo de tokens de LLMs sem perder o significado do prompt.</strong><br/>
  Otimizador com NLP para prompts do Claude, GPT-4 e Gemini — inglês e português.
</p>

<p align="center">
  <img src="https://img.shields.io/badge/python-3.14-blue?style=flat-square&logo=python&logoColor=white"/>
  <img src="https://img.shields.io/badge/license-MIT-green?style=flat-square"/>
  <img src="https://img.shields.io/badge/models-Claude%20%7C%20GPT--4%20%7C%20Gemini-6366f1?style=flat-square"/>
  <img src="https://img.shields.io/badge/languages-EN%20%7C%20PT-green?style=flat-square"/>
  <img src="https://img.shields.io/badge/tests-114%20passing-brightgreen?style=flat-square"/>
</p>

---

## O que faz

O TokenWise analisa seus prompts com técnicas de NLP e aplica uma cadeia de estratégias de otimização para reduzir a contagem de tokens — diminuindo os custos de API enquanto preserva a intenção. O idioma é detectado automaticamente.

```
Original   →  21 tokens   $0.000063
Otimizado  →   7 tokens   $0.000021   (66,7% de economia)
```

## Pipeline

Cada prompt passa por cinco estratégias em sequência, seguidas por um pós-processador que restaura pontuação, capitalização e contrações corretas.

| Etapa | Estratégia | Descrição |
|---|---|---|
| 1 | `whitespace_collapse` | Remove espaços redundantes e linhas em branco |
| 2 | `verbose_phrases` | Substitui expressões prolixas — padrões para EN e PT |
| 3 | `redundancy_removal` | Elimina frases duplicadas |
| 4 | `stopword_removal` | Remove palavras funcionais de baixo valor (NLTK) |
| ✦ | `postprocessor` | Corrige espaçamento de pontuação, capitalização e apóstrofos |

Dois presets integrados: **padrão** (todas as estratégias) e **conservador** (apenas espaços + frases prolixas + redundância).

## Suporte a idiomas

O idioma é detectado automaticamente via `langdetect`. Use `--lang` para forçar um idioma específico.

| Recurso | Inglês | Português |
|---|---|---|
| Remoção de stopwords | ✓ 179 palavras | ✓ 207 palavras |
| Substituição de frases prolixas | ✓ 18 padrões | ✓ 22 padrões |
| Remoção de redundâncias | ✓ | ✓ |

## Instalação

```bash
git clone https://github.com/Filip3Owl/TokenWise.git
cd TokenWise
python3 -m venv venv
source venv/bin/activate
pip install -e .
```

Isso instala `tokenwise` como um comando global — sem necessidade de chamar `python main.py` diretamente.

> **Nota no macOS:** Os dados do NLTK são baixados automaticamente na primeira execução.

## Uso

```bash
# Otimizar um prompt (idioma detectado automaticamente)
tokenwise "In order to make use of this feature, please be advised that you should provide assistance to the user."

# Forçar um idioma
tokenwise --lang pt "Com o objetivo de utilizar este recurso."
tokenwise --lang en "Your prompt here."

# Ler de um arquivo
tokenwise --file prompt.txt

# Segmentar um modelo específico
tokenwise --model gpt-4 "your prompt here"

# Modo conservador (sem remoção de stopwords ou lematização)
tokenwise --conservative "your prompt here"

# Salvar a saída otimizada em arquivo
tokenwise --file prompt.txt --output optimized.txt

# Exibir apenas o resultado, sem relatório
tokenwise --no-report "your prompt here"

# Saída JSON legível por máquina (para scripts / CI)
tokenwise --json "your prompt here"

# Enviar texto via stdin
echo "your prompt here" | tokenwise
cat prompt.txt | tokenwise
```

## Exemplo de saída

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

## Modelos suportados

**Anthropic**

| Modelo | Preço de entrada |
|---|---|
| `claude-opus-4-7` | $15,00 / 1M tokens |
| `claude-sonnet-4-6` | $3,00 / 1M tokens |
| `claude-haiku-4-5` | $0,80 / 1M tokens |

**OpenAI**

| Modelo | Preço de entrada |
|---|---|
| `gpt-4o` | $2,50 / 1M tokens |
| `gpt-4` | $30,00 / 1M tokens |
| `gpt-4o-mini` | $0,15 / 1M tokens |
| `gpt-3.5-turbo` | $0,50 / 1M tokens |
| `codex` / `text-davinci` | $2,00 / 1M tokens |

**Google Gemini**

| Modelo | Preço de entrada |
|---|---|
| `gemini-3-flash-preview` | $0,50 / 1M tokens |
| `gemini-2.0-flash` | $0,10 / 1M tokens |
| `gemini-1.5-flash` | $0,075 / 1M tokens |
| `gemini-1.5-pro` | $1,25 / 1M tokens |

O matching por prefixo é suportado — `claude`, `gpt-4`, `gemini-3`, `gemini` são resolvidos automaticamente.

## API REST

O TokenWise expõe um servidor FastAPI para que qualquer aplicação possa otimizar prompts — ou utilizá-lo como proxy transparente de LLM — via HTTP.

```bash
# Copiar e preencher suas chaves
cp .env.example .env

# Iniciar o servidor
uvicorn api.main:app --reload
```

Documentação interativa disponível em `http://127.0.0.1:8000/docs`.

### Modelo de autenticação

O TokenWise usa um sistema de autenticação em dois níveis:

| Tipo de token | Usado para | Configurado via |
|---|---|---|
| **Chave mestre** (`TOKENWISE_API_KEY`) | Apenas endpoints `/admin/*` | variável de ambiente |
| **Token de cliente** | `/optimize` e `/chat` | criado via `POST /admin/clients` |

Comece criando um token de cliente com a chave mestre e, em seguida, use esse token nas chamadas à API.

```bash
# Passo 1 — criar um cliente (executar uma vez)
curl -X POST http://127.0.0.1:8000/admin/clients \
  -H "Authorization: Bearer $TOKENWISE_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"name": "my-app", "plan": "basic"}'
# → retorna um campo token — salve-o

# Passo 2 — usar o token de cliente em todas as chamadas à API
Authorization: Bearer <client-token>
```

---

**`POST /admin/clients`** — cria um novo token de cliente.

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
  "token": "abc123XYZ...(texto completo — salve agora, não será exibido novamente)",
  "plan": "pro",
  "rate_limit": 300,
  "is_active": true,
  "created_at": "2026-05-18 10:00:00"
}
```

> **Salve o token imediatamente.** Ele é retornado completo apenas na criação. Chamadas subsequentes a `GET /admin/clients` exibem apenas os primeiros 8 caracteres (`abc123XY...`) — o valor completo nunca é armazenado no banco de dados.

**`GET /admin/clients`** — lista todos os clientes.

**`PATCH /admin/clients/{token}`** — atualiza plano ou limite de requisições.

**`DELETE /admin/clients/{token}`** — revoga um token de cliente.

---

**`POST /optimize`** — otimiza um prompt sem chamar nenhum LLM.

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

**`POST /chat`** — otimiza e encaminha ao LLM upstream, retornando sua resposta.

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

Modelos suportados: `claude-*` (requer `ANTHROPIC_API_KEY`) · `gpt-*` (requer `OPENAI_API_KEY`) · `gemini-*` (requer `GOOGLE_API_KEY`)

---

**`GET /health`** — retorna `{"status": "ok"}`.

### Campos da requisição

| Campo | Descrição |
|---|---|
| `text` | Prompt a otimizar — máximo de 10.000 caracteres (obrigatório) |
| `model` | Modelo alvo (padrão: `claude-sonnet-4-6`) |
| `lang` | `"auto"`, `"en"` ou `"pt"` (padrão: `"auto"`) |
| `conservative` | Ignorar remoção de stopwords (padrão: `false`) |

### Planos e limites de requisições

| Plano | Limite | Configurado via |
|---|---|---|
| `basic` (padrão) | 60 req / min | `"plan": "basic"` |
| `pro` | 300 req / min | `"plan": "pro"` |
| Personalizado | qualquer valor de 1 a 10.000 | `"rate_limit": <n>` |

Os limites são aplicados por token de cliente (janela deslizante), não por IP.

### Segurança

| Proteção | Detalhe |
|---|---|
| Autenticação admin | Variável de ambiente `TOKENWISE_API_KEY` mestre |
| Autenticação de cliente | Bearer token por cliente — armazenado como hash SHA-256, texto nunca persistido |
| Rate limiting | Janela deslizante por cliente (baseado no plano ou personalizado) |
| Limite de payload | Máximo de 10.000 caracteres |
| Timeout de LLM | 30 segundos |

## Executando os testes

```bash
python -m pytest tests/ -v
```

114 testes cobrindo tokenizer, NLP, estratégias, precificação, pós-processador, detecção de idioma, pipeline do otimizador, integração com a CLI (incluindo `--json`), API REST (autenticação, rate limiting, limite de payload, `/optimize`, `/chat` com LLM simulado) e endpoints de administração.

## Estrutura do projeto

```
TokenWise/
├── api/
│   ├── main.py            # App FastAPI: health, optimize, chat + roteador admin
│   ├── admin.py           # CRUD de /admin/clients (Fase C)
│   ├── auth.py            # require_admin_auth + require_client_auth + rate limiting
│   ├── database.py        # Client store SQLite (stdlib sqlite3)
│   ├── config.py          # Config central: limite de payload, timeout de LLM
│   ├── llm.py             # Cliente LLM upstream (Anthropic + OpenAI + Gemini)
│   └── schemas.py         # Modelos Pydantic de requisição/resposta
├── optimizer/
│   ├── core.py            # Pipeline do otimizador + detecção de idioma
│   ├── strategies.py      # Estratégias plugáveis com listas de frases EN/PT
│   ├── nlp.py             # Processamento NLTK (en + pt)
│   ├── tokenizer.py       # Contagem de tokens (tiktoken)
│   ├── pricing.py         # Cálculo de custo em USD por modelo
│   ├── postprocessor.py   # Correção de qualidade da saída (pontuação, capitalização)
│   └── models.py          # Tipos de dados
├── tests/
├── assets/
│   └── tokenwise_logo.svg
├── main.py
├── pyproject.toml
└── requirements.txt
```

## Roadmap

### Concluído
- Endpoint REST `POST /optimize` (FastAPI) ✓
- Endpoint proxy `POST /chat` — otimiza e encaminha para Claude / GPT / Gemini ✓
- Tokens de API por cliente com limites individuais de requisição (Fase C) ✓
  - Client store SQLite, CRUD em `/admin/clients`
  - Planos: `basic` (60 req/min) e `pro` (300 req/min), totalmente personalizáveis
  - Rate limiting por janela deslizante por cliente
  - Tokens armazenados como hashes SHA-256 — texto exibido apenas na criação
- Flag `--json` — saída JSON legível por máquina para scripts e pipelines de CI ✓

### Planejado
- Flag `--diff` — exibir exatamente o que mudou entre o original e o otimizado
- Suporte ao idioma espanhol (`es`)

## Licença

MIT
