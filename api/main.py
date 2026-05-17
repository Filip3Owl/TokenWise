"""
TokenWise FastAPI application.

Exposes the NLP-powered prompt optimizer as a REST API so that any service
can reduce its LLM token costs without changing its own codebase.

Endpoints:
    GET  /health    — liveness check
    POST /optimize  — optimize a prompt and return token/cost savings
    POST /chat      — (Phase B) optimize and forward to upstream LLM
"""

from fastapi import FastAPI, HTTPException, Depends, Request
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from optimizer.core import Optimizer
from .auth import require_auth
from .config import LLM_TIMEOUT_SECONDS
from .llm import call_llm
from .schemas import OptimizeRequest, OptimizeResponse, StrategyResultResponse, ChatRequest, ChatResponse

# Rate limiter keyed by client IP address.
# In-memory storage is used here; replace with Redis for multi-process deployments.
limiter = Limiter(key_func=get_remote_address)

app = FastAPI(
    title="TokenWise API",
    description="NLP-powered prompt optimizer — reduce token costs before calling LLM APIs.",
    version="1.0.0",
)

# Register the limiter and its 429 error handler with the app
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)


@app.get("/health")
def health():
    """Liveness check — returns 200 OK when the server is running."""
    return {"status": "ok"}


@app.post("/optimize", response_model=OptimizeResponse)
@limiter.limit("60/minute")
def optimize(request: Request, body: OptimizeRequest, _: None = Depends(require_auth)):
    """
    Optimize a prompt to reduce token consumption.

    Applies a pipeline of NLP strategies (whitespace collapse, verbose phrase
    replacement, redundancy removal, stopword removal) and returns the optimized
    text along with token counts, cost estimates, and a per-strategy breakdown.

    Rate limit: 60 requests per minute per IP.
    Authentication: Bearer token required (TOKENWISE_API_KEY).
    """
    try:
        # Build the optimizer with the requested preset (default or conservative)
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
@limiter.limit("60/minute")
def chat(request: Request, body: ChatRequest, _: None = Depends(require_auth)):
    """
    Optimize a prompt and forward it to the upstream LLM.

    This is the TokenWise proxy endpoint. The caller sends a prompt; TokenWise
    optimizes it, calls the appropriate LLM (Anthropic or OpenAI), and returns
    the LLM response alongside the optimization savings metadata.

    Supported models:
        - claude-* → Anthropic Messages API (requires ANTHROPIC_API_KEY)
        - gpt-*    → OpenAI Chat Completions API (requires OPENAI_API_KEY)

    Rate limit: 60 requests per minute per IP.
    Authentication: Bearer token required (TOKENWISE_API_KEY).
    """
    # Step 1: optimize the prompt using the same pipeline as /optimize
    optimizer = Optimizer(conservative=body.conservative)
    result = optimizer.optimize(body.text, model=body.model, lang=body.lang)

    # Step 2: forward the optimized prompt to the upstream LLM
    # call_llm raises HTTPException on timeout, auth failure, or unsupported model
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
