"""
ContextRefinery — Intent Agent

Analyzes the user's goal to produce a structured IntentAnalysis.
This is the first node in the LangGraph pipeline.
"""

from __future__ import annotations

import json
import time
import logging

from langchain_core.messages import SystemMessage, HumanMessage

from models.state import (
    RefineryState,
    IntentAnalysis,
    TaskType,
    AgentMessage,
    AgentStepType,
)
from agents.prompts import INTENT_ANALYSIS_SYSTEM, INTENT_USER_TEMPLATE

logger = logging.getLogger(__name__)


async def intent_agent_node(state: RefineryState) -> dict:
    """
    LangGraph node: Analyze the user's goal and source files to produce
    a structured intent analysis.
    
    Reads: user_goal, source_files
    Writes: intent_analysis, agent_messages
    """
    from main import get_llm  # Late import to avoid circular deps

    goal = state["user_goal"]
    source_files = state.get("source_files", [])

    # Build file context for the prompt
    file_list = "\n".join(
        f"- {f.filename} ({f.language}, {f.token_count} tokens)"
        for f in source_files
    ) or "No files provided."

    file_previews = "\n\n".join(
        f"### {f.filename}\n```{f.language}\n{f.content[:500]}{'...' if len(f.content) > 500 else ''}\n```"
        for f in source_files[:5]  # Limit to first 5 files for preview
    ) or "No file previews available."

    # Emit thinking message
    messages = [
        AgentMessage(
            step_type=AgentStepType.THINKING,
            agent_name="Intent Agent",
            content=f"Analyzing goal: \"{goal[:100]}{'...' if len(goal) > 100 else ''}\"",
            timestamp=time.time(),
            metadata={"files_count": len(source_files)},
        )
    ]

    try:
        llm = get_llm()

        user_prompt = INTENT_USER_TEMPLATE.format(
            goal=goal,
            file_list=file_list,
            file_previews=file_previews,
        )

        # Call the LLM
        response = await llm.ainvoke([
            SystemMessage(content=INTENT_ANALYSIS_SYSTEM),
            HumanMessage(content=user_prompt),
        ])

        # Parse the JSON response
        raw_json = response.content.strip()
        # Handle potential markdown code fences
        if raw_json.startswith("```"):
            raw_json = raw_json.split("\n", 1)[1].rsplit("```", 1)[0]

        parsed = json.loads(raw_json)

        try:
            task_type = TaskType(parsed.get("task_type", "general"))
        except ValueError:
            task_type = TaskType.GENERAL

        intent = IntentAnalysis(
            task_type=task_type,
            domain=parsed.get("domain", "general"),
            complexity=parsed.get("complexity", "medium"),
            key_concepts=parsed.get("key_concepts", []),
            constraints=parsed.get("constraints", []),
            suggested_cot_style=parsed.get("suggested_cot_style", "step-by-step"),
            few_shot_needed=parsed.get("few_shot_needed", False),
            summary=parsed.get("summary", goal),
        )

        messages.append(
            AgentMessage(
                step_type=AgentStepType.THINKING,
                agent_name="Intent Agent",
                content=(
                    f"✅ Intent classified: {intent.task_type.value} | "
                    f"Domain: {intent.domain} | "
                    f"Complexity: {intent.complexity} | "
                    f"CoT: {intent.suggested_cot_style}"
                ),
                timestamp=time.time(),
                metadata={"intent": parsed},
            )
        )

        return {
            "intent_analysis": intent,
            "agent_messages": messages,
        }

    except json.JSONDecodeError as e:
        logger.error(f"Intent Agent failed to parse LLM response: {e}")
        # Fallback to defaults
        fallback = IntentAnalysis(
            task_type=TaskType.GENERAL,
            domain="general",
            complexity="medium",
            key_concepts=[],
            constraints=[],
            suggested_cot_style="step-by-step",
            few_shot_needed=False,
            summary=goal,
        )
        messages.append(
            AgentMessage(
                step_type=AgentStepType.ERROR,
                agent_name="Intent Agent",
                content=f"⚠️ Could not parse intent, using defaults. Error: {str(e)}",
                timestamp=time.time(),
            )
        )
        return {
            "intent_analysis": fallback,
            "agent_messages": messages,
        }

    except Exception as e:
        logger.error(f"Intent Agent error: {e}")
        fallback = IntentAnalysis(
            task_type=TaskType.GENERAL,
            domain="general",
            complexity="medium",
            key_concepts=[],
            constraints=[],
            suggested_cot_style="step-by-step",
            few_shot_needed=False,
            summary=goal,
        )
        messages.append(
            AgentMessage(
                step_type=AgentStepType.ERROR,
                agent_name="Intent Agent",
                content=f"❌ Intent analysis failed: {str(e)}. Using defaults.",
                timestamp=time.time(),
            )
        )
        return {
            "intent_analysis": fallback,
            "agent_messages": messages,
        }
