"""
ContextRefinery — Refinery Agent

Constructs the optimized, context-dense prompt by injecting CoT scaffolding,
few-shot examples, and model-specific formatting based on the intent analysis
and retrieved context.
"""

from __future__ import annotations

import json
import time
import logging
from dataclasses import asdict

from langchain_core.messages import SystemMessage, HumanMessage

from models.state import (
    RefineryState,
    AgentMessage,
    AgentStepType,
)
from agents.prompts import (
    REFINERY_SYSTEM,
    REFINERY_USER_TEMPLATE,
    FEW_SHOT_INSTRUCTIONS,
    COT_DESCRIPTIONS,
)

logger = logging.getLogger(__name__)


async def refinery_agent_node(state: RefineryState) -> dict:
    """
    LangGraph node: Construct the refined, context-dense prompt.
    
    Reads: user_goal, intent_analysis, retrieved_context, token_budget, target_model, iteration
    Writes: refined_prompt, agent_messages, iteration
    """
    from main import get_llm  # Late import to avoid circular deps

    goal = state["user_goal"]
    intent = state["intent_analysis"]
    chunks = state.get("retrieved_context", [])
    token_budget = state["token_budget"]
    target_model = state["target_model"]
    iteration = state.get("iteration", 0) + 1

    messages = [
        AgentMessage(
            step_type=AgentStepType.REFINING,
            agent_name="Refinery Agent",
            content=f"🔧 Constructing prompt (iteration {iteration}) for {target_model}...",
            timestamp=time.time(),
            metadata={"iteration": iteration, "context_chunks": len(chunks)},
        )
    ]

    # Build context string from retrieved chunks
    context_str = "\n\n".join(
        f"--- Chunk {i+1} (from {chunk.source_file}, lines {chunk.start_line}-{chunk.end_line}, "
        f"relevance: {chunk.rerank_score:.3f}) ---\n{chunk.content}"
        for i, chunk in enumerate(chunks)
    ) or "No context chunks retrieved."

    # Calculate rough current token count
    current_tokens = sum(c.token_count for c in chunks) + len(goal.split()) * 2

    # Prepare the system prompt with parameters
    cot_style = intent.suggested_cot_style if intent else "step-by-step"
    few_shot_needed = intent.few_shot_needed if intent else False

    system_prompt = REFINERY_SYSTEM.format(
        cot_style=COT_DESCRIPTIONS.get(cot_style, COT_DESCRIPTIONS["step-by-step"]),
        few_shot_instruction=FEW_SHOT_INSTRUCTIONS[few_shot_needed],
        token_budget=token_budget,
        current_tokens=current_tokens,
        target_model=target_model,
    )

    user_prompt = REFINERY_USER_TEMPLATE.format(
        intent_json=json.dumps(asdict(intent), indent=2, default=str) if intent else "{}",
        goal=goal,
        context_chunks=context_str,
        token_budget=token_budget,
        target_model=target_model,
        cot_style=cot_style,
        few_shot_needed=few_shot_needed,
    )

    try:
        llm = get_llm()

        response = await llm.ainvoke([
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_prompt),
        ])

        refined_prompt = response.content.strip()

        messages.append(
            AgentMessage(
                step_type=AgentStepType.REFINING,
                agent_name="Refinery Agent",
                content=(
                    f"✅ Prompt constructed ({len(refined_prompt.split())} words, "
                    f"~{len(refined_prompt) // 4} tokens estimated)"
                ),
                timestamp=time.time(),
                metadata={
                    "prompt_length": len(refined_prompt),
                    "iteration": iteration,
                },
            )
        )

        return {
            "refined_prompt": refined_prompt,
            "iteration": iteration,
            "agent_messages": messages,
        }

    except Exception as e:
        logger.error(f"Refinery Agent error: {e}")
        # Fallback: construct a basic prompt from the raw inputs
        fallback_prompt = _build_fallback_prompt(goal, chunks, target_model, cot_style)

        messages.append(
            AgentMessage(
                step_type=AgentStepType.ERROR,
                agent_name="Refinery Agent",
                content=f"⚠️ LLM call failed, using template fallback: {str(e)}",
                timestamp=time.time(),
            )
        )

        return {
            "refined_prompt": fallback_prompt,
            "iteration": iteration,
            "agent_messages": messages,
        }


def _build_fallback_prompt(
    goal: str,
    chunks: list,
    target_model: str,
    cot_style: str,
) -> str:
    """Build a basic prompt without LLM assistance as a fallback."""

    context_section = "\n\n".join(
        f"```\n# From: {c.source_file} (lines {c.start_line}-{c.end_line})\n{c.content}\n```"
        for c in chunks
    )

    cot_instruction = {
        "step-by-step": "Think through this step-by-step before providing your answer.",
        "tree-of-thought": "Consider multiple approaches, evaluate the tradeoffs, then select the best.",
        "chain-of-verification": "After answering, verify each claim against the provided context.",
    }.get(cot_style, "Think carefully before responding.")

    return f"""You are an expert software engineer. Help the user with the following goal.

## Goal
{goal}

## Relevant Context
{context_section}

## Instructions
{cot_instruction}

Provide a thorough, well-structured response based on the context provided above."""
