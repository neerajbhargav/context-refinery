"""
ContextRefinery — LangGraph State Machine

Defines the core prompt refinement pipeline as a LangGraph StateGraph:

  __start__ → intent_agent → hybrid_retrieve → refinery_agent → evaluate
                                                     ↑              │
                                                     └──── (loop) ──┘
                                                              │
                                                          __end__
"""

from __future__ import annotations

import time
import logging
from typing import Literal

from langgraph.graph import StateGraph, END, START

from models.state import (
    RefineryState,
    AgentMessage,
    AgentStepType,
    EvalScores,
)
from agents.intent_agent import intent_agent_node
from agents.refinery_agent import refinery_agent_node
from config import settings

logger = logging.getLogger(__name__)


# ── Hybrid Retrieve Node ───────────────────────────────────────────────


async def hybrid_retrieve_node(state: RefineryState) -> dict:
    """
    LangGraph node: Retrieve the most relevant context chunks using
    hybrid search (BM25 + Dense) with cross-encoder reranking.

    Reads: user_goal, intent_analysis, source_files, token_budget
    Writes: retrieved_context, agent_messages
    """
    from retriever.hybrid import hybrid_retrieve

    goal = state["user_goal"]
    intent = state.get("intent_analysis")
    token_budget = state["token_budget"]
    source_files = state.get("source_files", [])

    messages = [
        AgentMessage(
            step_type=AgentStepType.RETRIEVING,
            agent_name="Hybrid Retriever",
            content=f"🔍 Searching {len(source_files)} files for relevant context...",
            timestamp=time.time(),
        )
    ]

    try:
        # Build the query from the goal + key concepts
        query = goal
        if intent and intent.key_concepts:
            query += " " + " ".join(intent.key_concepts)

        chunks = await hybrid_retrieve(
            query=query,
            source_files=source_files,
            token_budget=token_budget,
            top_k=settings.RERANKER_TOP_K,
        )

        total_tokens = sum(c.token_count for c in chunks)

        messages.append(
            AgentMessage(
                step_type=AgentStepType.RETRIEVING,
                agent_name="Hybrid Retriever",
                content=(
                    f"✅ Retrieved {len(chunks)} chunks "
                    f"({total_tokens}/{token_budget} tokens used)"
                ),
                timestamp=time.time(),
                metadata={
                    "chunks": len(chunks),
                    "tokens_used": total_tokens,
                    "budget": token_budget,
                },
            )
        )

        return {
            "retrieved_context": chunks,
            "agent_messages": messages,
        }

    except Exception as e:
        logger.error(f"Hybrid retrieval error: {e}")
        messages.append(
            AgentMessage(
                step_type=AgentStepType.ERROR,
                agent_name="Hybrid Retriever",
                content=f"❌ Retrieval failed: {str(e)}. Proceeding with empty context.",
                timestamp=time.time(),
            )
        )
        return {
            "retrieved_context": [],
            "agent_messages": messages,
        }


# ── Evaluate Node ──────────────────────────────────────────────────────


async def evaluate_node(state: RefineryState) -> dict:
    """
    LangGraph node: Score the refined prompt for context grounding,
    budget utilization, and information density.

    Reads: refined_prompt, retrieved_context, token_budget, user_goal
    Writes: eval_scores, agent_messages, status
    """
    from eval.evaluator import evaluate_prompt

    prompt = state.get("refined_prompt", "")
    chunks = state.get("retrieved_context", [])
    budget = state["token_budget"]
    goal = state["user_goal"]

    messages = [
        AgentMessage(
            step_type=AgentStepType.EVALUATING,
            agent_name="Eval Lab",
            content="📊 Scoring prompt for context grounding...",
            timestamp=time.time(),
        )
    ]

    try:
        scores = await evaluate_prompt(
            prompt=prompt,
            context_chunks=[c.content for c in chunks],
            goal=goal,
            token_budget=budget,
        )

        status_emoji = "✅" if scores.passed else "⚠️"
        messages.append(
            AgentMessage(
                step_type=AgentStepType.EVALUATING,
                agent_name="Eval Lab",
                content=(
                    f"{status_emoji} Grounding: {scores.context_grounding:.0%} | "
                    f"Density: {scores.information_density:.0%} | "
                    f"Budget: {scores.budget_utilization:.0%} | "
                    f"Overall: {scores.overall_score:.0%} | "
                    f"{'PASS' if scores.passed else 'NEEDS REFINEMENT'}"
                ),
                timestamp=time.time(),
                metadata={
                    "grounding": scores.context_grounding,
                    "density": scores.information_density,
                    "utilization": scores.budget_utilization,
                    "overall": scores.overall_score,
                    "passed": scores.passed,
                },
            )
        )

        return {
            "eval_scores": scores,
            "agent_messages": messages,
        }

    except Exception as e:
        logger.error(f"Evaluation error: {e}")
        fallback_scores = EvalScores(
            context_grounding=0.5,
            budget_utilization=0.5,
            information_density=0.5,
            overall_score=0.5,
            passed=True,  # Don't block on eval failure
            details={"error": str(e)},
        )
        messages.append(
            AgentMessage(
                step_type=AgentStepType.ERROR,
                agent_name="Eval Lab",
                content=f"⚠️ Evaluation error: {str(e)}. Passing with default scores.",
                timestamp=time.time(),
            )
        )
        return {
            "eval_scores": fallback_scores,
            "agent_messages": messages,
        }


# ── Conditional Edge ───────────────────────────────────────────────────


def should_refine_again(state: RefineryState) -> Literal["refinery_agent", "__end__"]:
    """
    Conditional edge: decide whether to loop back to the refinery agent
    or finish the pipeline.

    Loops back if:
      - eval score is below the threshold AND
      - we haven't exceeded max iterations
    """
    scores = state.get("eval_scores")
    iteration = state.get("iteration", 0)
    max_iter = settings.EVAL_MAX_ITERATIONS

    if scores is None:
        return END

    if not scores.passed and iteration < max_iter:
        logger.info(
            f"Eval score {scores.overall_score:.2f} below threshold, "
            f"iteration {iteration}/{max_iter} — refining again"
        )
        return "refinery_agent"

    return END


# ── Graph Builder ──────────────────────────────────────────────────────


def build_refinery_graph() -> StateGraph:
    """
    Construct and compile the LangGraph state machine for prompt refinement.
    
    Returns a compiled graph ready for invocation.
    """
    builder = StateGraph(RefineryState)

    # Add nodes
    builder.add_node("intent_agent", intent_agent_node)
    builder.add_node("hybrid_retrieve", hybrid_retrieve_node)
    builder.add_node("refinery_agent", refinery_agent_node)
    builder.add_node("evaluate", evaluate_node)

    # Add edges (linear pipeline with eval feedback loop)
    builder.add_edge(START, "intent_agent")
    builder.add_edge("intent_agent", "hybrid_retrieve")
    builder.add_edge("hybrid_retrieve", "refinery_agent")
    builder.add_edge("refinery_agent", "evaluate")

    # Conditional edge: loop back or finish
    builder.add_conditional_edges(
        "evaluate",
        should_refine_again,
        {
            "refinery_agent": "refinery_agent",
            END: END,
        },
    )

    graph = builder.compile()
    logger.info("✅ LangGraph refinery pipeline compiled successfully")

    return graph
