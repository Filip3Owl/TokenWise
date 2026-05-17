from fastapi import FastAPI, HTTPException, Depends

from optimizer.core import Optimizer
from .auth import require_auth
from .schemas import OptimizeRequest, OptimizeResponse, StrategyResultResponse

app = FastAPI(
    title="TokenWise API",
    description="NLP-powered prompt optimizer — reduce token costs before calling LLM APIs.",
    version="1.0.0",
)


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/optimize", response_model=OptimizeResponse)
def optimize(request: OptimizeRequest, _: None = Depends(require_auth)):
    try:
        optimizer = Optimizer(conservative=request.conservative)
        result = optimizer.optimize(request.text, model=request.model, lang=request.lang)
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
