"""
TokenWise FastAPI application.

Exposes the NLP-powered prompt optimizer as a REST API so that any service
can reduce its LLM token costs without changing its own codebase.

Endpoints:
    GET    /health              — liveness check
    POST   /optimize            — optimize a prompt and return token/cost savings
    POST   /chat                — (Phase B) optimize and forward to upstream LLM
    POST   /admin/clients       — (Phase C) create a per-client API token
    GET    /admin/clients       — (Phase C) list all clients
    PATCH  /admin/clients/{t}   — (Phase C) update a client's plan/rate_limit
    DELETE /admin/clients/{t}   — (Phase C) revoke a client token
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
    description="NLP-powered prompt optimizer — reduce token costs before calling LLM APIs.",
    version="1.0.0",
    lifespan=lifespan,
)

app.include_router(admin_router)


@app.get("/health")
def health():
    """Liveness check — returns 200 OK when the server is running."""
    return {"status": "ok"}


@app.post("/optimize", response_model=OptimizeResponse)
def optimize(request: Request, body: OptimizeRequest, client: dict = Depends(require_client_auth)):
    """
    Optimize a prompt to reduce token consumption.

    Applies a pipeline of NLP strategies (whitespace collapse, verbose phrase
    replacement, redundancy removal, stopword removal) and returns the optimized
    text along with token counts, cost estimates, and a per-strategy breakdown.

    Authentication: per-client Bearer token (managed via /admin/clients).
    Rate limit: per-client (basic=60 req/min, pro=300 req/min).
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
    Optimize a prompt and forward it to the upstream LLM.

    This is the TokenWise proxy endpoint. The caller sends a prompt; TokenWise
    optimizes it, calls the appropriate LLM (Anthropic, OpenAI, or Google Gemini),
    and returns the LLM response alongside the optimization savings metadata.

    Supported models:
        - claude-* → Anthropic Messages API (requires ANTHROPIC_API_KEY)
        - gpt-*    → OpenAI Chat Completions API (requires OPENAI_API_KEY)
        - gemini-* → Google Gemini API (requires GOOGLE_API_KEY)

    Authentication: per-client Bearer token (managed via /admin/clients).
    Rate limit: per-client (basic=60 req/min, pro=300 req/min).
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
