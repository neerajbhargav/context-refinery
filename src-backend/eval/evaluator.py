"""
ContextRefinery — Prompt Evaluator

Scores a refined prompt for context grounding, information density,
and budget utilization. Uses lightweight heuristic scoring that
works locally without an external LLM dependency.

Optional RAGAS integration available when an API key is configured.
"""

from __future__ import annotations

import logging
from collections import Counter

from models.state import EvalScores
from services.token_counter import count_tokens
from eval.metrics import (
    compute_context_grounding,
    compute_information_density,
    compute_budget_utilization,
)
from config import settings

logger = logging.getLogger(__name__)


async def evaluate_prompt(
    prompt: str,
    context_chunks: list[str],
    goal: str,
    token_budget: int,
) -> EvalScores:
    """
    Evaluate the refined prompt across three dimensions:
    
    1. Context Grounding — % of prompt content traceable to source chunks
    2. Information Density — unique information per token
    3. Budget Utilization — how efficiently the token budget is used
    
    Args:
        prompt: The refined prompt to evaluate
        context_chunks: The source context chunks used
        goal: The original user goal
        token_budget: The target token budget
    
    Returns:
        EvalScores with per-metric scores and pass/fail determination
    """
    if not prompt:
        return EvalScores(passed=False, details={"error": "Empty prompt"})

    # Compute individual metrics
    grounding = compute_context_grounding(prompt, context_chunks)
    density = compute_information_density(prompt)
    utilization = compute_budget_utilization(prompt, token_budget)

    # Weighted average for overall score
    overall = (
        grounding * 0.50 +     # Grounding is most important
        density * 0.25 +       # Density matters for efficiency
        utilization * 0.25     # Budget adherence
    )

    passed = overall >= settings.EVAL_GROUNDING_THRESHOLD

    scores = EvalScores(
        context_grounding=round(grounding, 4),
        budget_utilization=round(utilization, 4),
        information_density=round(density, 4),
        overall_score=round(overall, 4),
        passed=passed,
        details={
            "prompt_tokens": count_tokens(prompt),
            "budget": token_budget,
            "threshold": settings.EVAL_GROUNDING_THRESHOLD,
            "context_chunks_used": len(context_chunks),
        },
    )

    logger.info(
        f"Eval: grounding={grounding:.2%} density={density:.2%} "
        f"utilization={utilization:.2%} overall={overall:.2%} "
        f"{'PASS' if passed else 'FAIL'}"
    )

    return scores
