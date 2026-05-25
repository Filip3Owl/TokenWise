"""
Aplicação FastAPI do TokenWise.

Expõe o otimizador de prompts com NLP como uma API REST para que qualquer serviço
possa reduzir seus custos de tokens de LLM sem alterar seu próprio código.

Endpoints:
    GET    /health              — verificação de disponibilidade
    POST   /optimize            — otimiza um prompt e retorna economia de tokens/custo
    POST   /chat                — (Fase B) otimiza e encaminha ao LLM upstream
    POST   /admin/clients       — (Fase C) cria um token de API por cliente
    GET    /admin/clients       — (Fase C) lista todos os clientes
    PATCH  /admin/clients/{t}   — (Fase C) atualiza plano/rate_limit de um cliente
    DELETE /admin/clients/{t}   — (Fase C) revoga um token de cliente
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Depends, Request

from optimizer.core import Optimizer
from .admin import router as admin_router
from .auth import require_client_auth
from .database import init_db
from .llm import call_llm
from .schemas import OptimizeRequest, OptimizeResponse, StrategyResultResponse, ChatRequest, ChatResponse


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


app = FastAPI(
    title="TokenWise API",
    description="Otimizador de prompts com NLP — reduza custos de tokens antes de chamar APIs de LLM.",
    version="1.0.0",
    lifespan=lifespan,
)

app.include_router(admin_router)


@app.get("/health")
def health():
    """Verificação de disponibilidade — retorna 200 OK quando o servidor está ativo."""
    return {"status": "ok"}


@app.post("/optimize", response_model=OptimizeResponse)
def optimize(request: Request, body: OptimizeRequest, client: dict = Depends(require_client_auth)):
    """
    Otimiza um prompt para reduzir o consumo de tokens.

    Aplica um pipeline de estratégias de NLP (colapso de espaços, substituição de frases
    prolixas, remoção de redundâncias, remoção de stopwords) e retorna o texto otimizado
    com contagem de tokens, estimativas de custo e breakdown por estratégia.

    Autenticação: Bearer token por cliente (gerenciado via /admin/clients).
    Rate limit: por cliente (basic=60 req/min, pro=300 req/min).
    """
    try:
        optimizer = Optimizer(conservative=body.conservative)
        result = optimizer.optimize(body.text, model=body.model, lang=body.lang)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))

    return OptimizeResponse(
        original_text=result.original_text,
        optimized_text=result.optimized_text,
        original_tokens=result.original_tokens,
        final_tokens=result.final_tokens,
        tokens_saved=result.tokens_saved,
        savings_pct=round(result.savings_pct, 2),
        model=result.model,
        lang=result.lang,
        original_cost=result.original_cost,
        final_cost=result.final_cost,
        cost_saved=result.cost_saved,
        cost_savings_pct=round(result.cost_savings_pct, 2),
        strategies=[
            StrategyResultResponse(
                name=s.name,
                tokens_saved=s.tokens_saved,
                applied=s.applied,
            )
            for s in result.strategy_results
        ],
    )


@app.post("/chat", response_model=ChatResponse)
def chat(request: Request, body: ChatRequest, client: dict = Depends(require_client_auth)):
    """
    Otimiza um prompt e o encaminha ao LLM upstream.

    Este é o endpoint proxy do TokenWise. O chamador envia um prompt; o TokenWise
    o otimiza, chama o LLM adequado (Anthropic, OpenAI ou Google Gemini) e retorna
    a resposta do LLM junto com os metadados de economia da otimização.

    Modelos suportados:
        - claude-* → Anthropic Messages API (requer ANTHROPIC_API_KEY)
        - gpt-*    → OpenAI Chat Completions API (requer OPENAI_API_KEY)
        - gemini-* → Google Gemini API (requer GOOGLE_API_KEY)

    Autenticação: Bearer token por cliente (gerenciado via /admin/clients).
    Rate limit: por cliente (basic=60 req/min, pro=300 req/min).
    """
    optimizer = Optimizer(conservative=body.conservative)
    result = optimizer.optimize(body.text, model=body.model, lang=body.lang)

    llm_response = call_llm(result.optimized_text, model=body.model)

    return ChatResponse(
        llm_response=llm_response,
        original_tokens=result.original_tokens,
        final_tokens=result.final_tokens,
        tokens_saved=result.tokens_saved,
        savings_pct=round(result.savings_pct, 2),
        original_cost=result.original_cost,
        final_cost=result.final_cost,
        cost_saved=result.cost_saved,
        cost_savings_pct=round(result.cost_savings_pct, 2),
        model=result.model,
        lang=result.lang,
    )
