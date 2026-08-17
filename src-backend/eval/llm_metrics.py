"""Optional DeepEval / RAGAS path.

Local heuristic metrics always run. This module only activates when:
  1. a cloud API key is configured, and
  2. the matching optional package is installed.

Missing extras or missing keys are not errors. The local loop keeps working.
Install the extras with:  pip install 'deepeval>=2.9' 'ragas>=0.2'
"""

from __future__ import annotations

import asyncio
import logging
import os
from typing import Any

from config import settings

logger = logging.getLogger(__name__)


def llm_eval_available() -> bool:
    """True when a cloud key is set. Packages are imported lazily."""
    return bool(settings.OPENAI_API_KEY or settings.ANTHROPIC_API_KEY or settings.GOOGLE_API_KEY)


def _ensure_openai_env() -> None:
    # DeepEval and RAGAS both read OPENAI_API_KEY from the environment by default.
    if settings.OPENAI_API_KEY and not os.environ.get("OPENAI_API_KEY"):
        os.environ["OPENAI_API_KEY"] = settings.OPENAI_API_KEY


def _run_deepeval(goal: str, prompt: str, context_chunks: list[str]) -> dict[str, Any] | None:
    try:
        from deepeval.metrics import AnswerRelevancyMetric, FaithfulnessMetric
        from deepeval.test_case import LLMTestCase
    except ImportError:
        logger.info("deepeval not installed; skipping DeepEval metrics")
        return None

    _ensure_openai_env()
    test_case = LLMTestCase(
        input=goal or "Refine the retrieved context into a grounded prompt.",
        actual_output=prompt,
        retrieval_context=context_chunks or [""],
    )
    faithfulness = FaithfulnessMetric(threshold=0.7, include_reason=True)
    relevancy = AnswerRelevancyMetric(threshold=0.7, include_reason=True)
    faithfulness.measure(test_case)
    relevancy.measure(test_case)
    return {
        "backend": "deepeval",
        "faithfulness": float(faithfulness.score or 0.0),
        "answer_relevancy": float(relevancy.score or 0.0),
        "faithfulness_reason": getattr(faithfulness, "reason", None),
        "relevancy_reason": getattr(relevancy, "reason", None),
    }


def _run_ragas(goal: str, prompt: str, context_chunks: list[str]) -> dict[str, Any] | None:
    try:
        from ragas import evaluate
        from ragas.metrics import answer_relevancy, faithfulness
    except ImportError:
        logger.info("ragas not installed; skipping RAGAS metrics")
        return None

    _ensure_openai_env()
    try:
        from datasets import Dataset
    except ImportError:
        logger.info("datasets not installed; skipping RAGAS metrics")
        return None

    dataset = Dataset.from_dict(
        {
            "question": [goal or "Refine the retrieved context into a grounded prompt."],
            "answer": [prompt],
            "contexts": [context_chunks or [""]],
        }
    )
    result = evaluate(dataset, metrics=[faithfulness, answer_relevancy])
    row = result.to_pandas().iloc[0].to_dict()
    return {
        "backend": "ragas",
        "faithfulness": float(row.get("faithfulness") or 0.0),
        "answer_relevancy": float(row.get("answer_relevancy") or row.get("response_relevancy") or 0.0),
    }


async def maybe_llm_eval(
    prompt: str,
    context_chunks: list[str],
    goal: str,
) -> dict[str, Any] | None:
    """Run DeepEval first, then RAGAS, if a cloud key is configured.

    Returns a score dict or None when the optional path is inactive or fails.
    Never raises into the local refinement loop.
    """
    if not llm_eval_available():
        return None

    def _run() -> dict[str, Any] | None:
        deepeval_scores = _run_deepeval(goal, prompt, context_chunks)
        if deepeval_scores is not None:
            return deepeval_scores
        return _run_ragas(goal, prompt, context_chunks)

    try:
        return await asyncio.to_thread(_run)
    except Exception:
        logger.exception("optional LLM eval failed; continuing with local metrics")
        return None
