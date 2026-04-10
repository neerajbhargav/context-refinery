"""
ContextRefinery — Eval Router

Endpoint for standalone prompt evaluation.
"""

from __future__ import annotations

import logging
from dataclasses import asdict

from fastapi import APIRouter, HTTPException

from models.schemas import EvalRequest, EvalScoresResponse
from eval.evaluator import evaluate_prompt

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/eval", tags=["eval"])


@router.post("/score", response_model=EvalScoresResponse)
async def score_prompt(request: EvalRequest):
    """
    Score a prompt for context grounding, information density,
    and budget utilization.
    """
    try:
        scores = await evaluate_prompt(
            prompt=request.prompt,
            context_chunks=request.context_chunks,
            goal=request.goal,
            token_budget=request.token_budget,
        )

        return EvalScoresResponse(
            context_grounding=scores.context_grounding,
            budget_utilization=scores.budget_utilization,
            information_density=scores.information_density,
            overall_score=scores.overall_score,
            passed=scores.passed,
        )

    except Exception as e:
        logger.error(f"Evaluation error: {e}")
        raise HTTPException(status_code=500, detail=f"Evaluation failed: {str(e)}")
