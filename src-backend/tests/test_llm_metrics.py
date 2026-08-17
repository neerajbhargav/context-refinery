"""Prove the optional DeepEval / RAGAS hook exists and fails closed.

Stubs `config` so tests do not load pydantic_core (blocked in some sandboxes).
"""

from __future__ import annotations

import sys
import types
from pathlib import Path

import pytest

BACKEND = Path(__file__).resolve().parents[1]
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))

# Stub settings before importing the module under test.
_cfg = types.ModuleType("config")

class _Settings:
    OPENAI_API_KEY = None
    ANTHROPIC_API_KEY = None
    GOOGLE_API_KEY = None

_cfg.settings = _Settings()
sys.modules["config"] = _cfg

from eval.llm_metrics import maybe_llm_eval, _run_deepeval, llm_eval_available  # noqa: E402


@pytest.mark.asyncio
async def test_no_key_returns_none():
    _cfg.settings.OPENAI_API_KEY = None
    _cfg.settings.ANTHROPIC_API_KEY = None
    _cfg.settings.GOOGLE_API_KEY = None
    assert llm_eval_available() is False
    assert await maybe_llm_eval("prompt", ["chunk"], "goal") is None


def test_deepeval_import_miss_returns_none():
    sys.modules.pop("deepeval", None)
    sys.modules.pop("deepeval.metrics", None)
    sys.modules.pop("deepeval.test_case", None)
    result = _run_deepeval("goal", "prompt", ["chunk"])
    assert result is None


def test_deepeval_mocked_scores():
    metrics_mod = types.ModuleType("deepeval.metrics")
    test_case_mod = types.ModuleType("deepeval.test_case")
    root = types.ModuleType("deepeval")

    class FakeMetric:
        def __init__(self, *a, **k):
            self.score = 0.91
            self.reason = "grounded"

        def measure(self, test_case):
            return self.score

    class FakeTestCase:
        def __init__(self, **kwargs):
            self.kwargs = kwargs

    metrics_mod.FaithfulnessMetric = FakeMetric
    metrics_mod.AnswerRelevancyMetric = FakeMetric
    test_case_mod.LLMTestCase = FakeTestCase
    sys.modules["deepeval"] = root
    sys.modules["deepeval.metrics"] = metrics_mod
    sys.modules["deepeval.test_case"] = test_case_mod

    scores = _run_deepeval("goal", "prompt", ["chunk"])
    assert scores["backend"] == "deepeval"
    assert scores["faithfulness"] == 0.91
    assert scores["answer_relevancy"] == 0.91
