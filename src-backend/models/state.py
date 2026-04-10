"""
ContextRefinery — LangGraph State Definitions

Defines the shared state schema that flows through the LangGraph 
state machine. Each node reads from and writes to this state.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TypedDict, Annotated, Literal
from enum import Enum
import operator


# ── Enums ───────────────────────────────────────────────────────────────


class TaskType(str, Enum):
    """Classification of the user's goal."""
    CODE_GENERATION = "code_generation"
    DEBUGGING = "debugging"
    REFACTORING = "refactoring"
    DOCUMENTATION = "documentation"
    ANALYSIS = "analysis"
    CREATIVE = "creative"
    GENERAL = "general"


class AgentStepType(str, Enum):
    """Types of streaming events from agents."""
    THINKING = "thinking"
    RETRIEVING = "retrieving"
    REFINING = "refining"
    EVALUATING = "evaluating"
    COMPLETE = "complete"
    ERROR = "error"


# ── Data Classes ────────────────────────────────────────────────────────


@dataclass
class SourceFile:
    """A file ingested into the workbench."""
    path: str
    filename: str
    language: str
    content: str
    token_count: int
    chunk_ids: list[str] = field(default_factory=list)


@dataclass
class Chunk:
    """A retrieved context chunk with relevance scoring."""
    id: str
    content: str
    source_file: str
    start_line: int
    end_line: int
    token_count: int
    dense_score: float = 0.0
    bm25_score: float = 0.0
    rrf_score: float = 0.0
    rerank_score: float = 0.0


@dataclass
class IntentAnalysis:
    """Structured output from the Intent Agent."""
    task_type: TaskType
    domain: str
    complexity: Literal["low", "medium", "high"]
    key_concepts: list[str]
    constraints: list[str]
    suggested_cot_style: Literal["step-by-step", "tree-of-thought", "chain-of-verification"]
    few_shot_needed: bool
    summary: str


@dataclass
class EvalScores:
    """Evaluation scores for the refined prompt."""
    context_grounding: float = 0.0       # 0.0 - 1.0
    budget_utilization: float = 0.0      # 0.0 - 1.0
    information_density: float = 0.0     # 0.0 - 1.0
    overall_score: float = 0.0           # weighted average
    passed: bool = False
    details: dict = field(default_factory=dict)


@dataclass
class AgentMessage:
    """A message from an agent for the streaming UI."""
    step_type: AgentStepType
    agent_name: str
    content: str
    timestamp: float = 0.0
    metadata: dict = field(default_factory=dict)


# ── LangGraph State ────────────────────────────────────────────────────


class RefineryState(TypedDict):
    """
    The shared state for the LangGraph prompt refinement pipeline.
    
    This state flows through:
      __start__ → intent_agent → hybrid_retrieve → refinery_agent → evaluate → (__end__ | refinery_agent)
    """

    # ── Input (set once at start) ───────────────────────────────────
    user_goal: str
    source_files: list[SourceFile]
    token_budget: int
    target_model: Literal["gpt-4o", "claude-sonnet", "claude-opus", "gemini-pro", "gemini-flash", "ollama"]

    # ── Intent Agent Output ─────────────────────────────────────────
    intent_analysis: IntentAnalysis | None

    # ── Retriever Output ────────────────────────────────────────────
    retrieved_context: list[Chunk]

    # ── Refinery Agent Output ───────────────────────────────────────
    refined_prompt: str

    # ── Eval Output ─────────────────────────────────────────────────
    eval_scores: EvalScores | None

    # ── Streaming / Metadata ────────────────────────────────────────
    # Using Annotated with operator.add so messages accumulate across nodes
    agent_messages: Annotated[list[AgentMessage], operator.add]
    iteration: int
    status: Literal["idle", "running", "complete", "error"]
    error: str | None
