"""
ContextRefinery — Pydantic API Schemas

Request/response models for the FastAPI endpoints.
"""

from __future__ import annotations

from pydantic import BaseModel, Field
from typing import Literal
from enum import Enum


# ── Enums ───────────────────────────────────────────────────────────────


class TargetModel(str, Enum):
    GPT_4O = "gpt-4o"
    CLAUDE_SONNET = "claude-sonnet"
    CLAUDE_OPUS = "claude-opus"
    GEMINI_PRO = "gemini-pro"
    GEMINI_FLASH = "gemini-flash"
    OLLAMA = "ollama"


class SSEEventType(str, Enum):
    AGENT_MESSAGE = "agent_message"
    PROGRESS = "progress"
    RESULT = "result"
    EVAL = "eval"
    ERROR = "error"
    DONE = "done"


# ── Request Models ──────────────────────────────────────────────────────


class FileInput(BaseModel):
    """A file submitted for context extraction."""
    path: str
    filename: str
    content: str
    language: str = "text"


class RefineRequest(BaseModel):
    """Request to start a prompt refinement session."""
    goal: str = Field(..., min_length=10, description="The user's intent / goal description")
    project_id: str | None = Field(default=None, description="The unique project ID (if available)")
    files: list[FileInput] = Field(default_factory=list, description="Source files for context")
    token_budget: int = Field(default=4096, ge=512, le=32768)
    target_model: TargetModel = TargetModel.GEMINI_PRO
    max_iterations: int = Field(default=3, ge=1, le=5)


class IndexRequest(BaseModel):
    """Request to index a project folder."""
    project_name: str = Field(..., min_length=1)
    folder_path: str
    extensions: list[str] | None = None  # None = use defaults from config


class TokenCountRequest(BaseModel):
    """Request to count tokens in text."""
    text: str
    model: str = "gpt-4o"


class EvalRequest(BaseModel):
    """Request to evaluate a prompt against its source context."""
    prompt: str
    context_chunks: list[str]
    goal: str
    token_budget: int = 4096


# ── Response Models ─────────────────────────────────────────────────────


class HealthResponse(BaseModel):
    status: str = "ok"
    version: str = "0.1.0"
    llm_provider: str
    embedding_provider: str


class IndexResponse(BaseModel):
    project_name: str
    files_indexed: int
    chunks_created: int
    total_tokens: int


class SSEEvent(BaseModel):
    """Server-Sent Event payload."""
    event_type: SSEEventType
    data: dict
    timestamp: float


class RefineResult(BaseModel):
    """Final result of the refinement pipeline."""
    refined_prompt: str
    token_count: int
    token_budget: int
    target_model: str
    iterations: int
    eval_scores: EvalScoresResponse


class EvalScoresResponse(BaseModel):
    context_grounding: float = Field(..., ge=0.0, le=1.0)
    budget_utilization: float = Field(..., ge=0.0, le=1.0)
    information_density: float = Field(..., ge=0.0, le=1.0)
    overall_score: float = Field(..., ge=0.0, le=1.0)
    passed: bool


class ProjectInfo(BaseModel):
    """Info about an indexed project."""
    name: str
    folder_path: str
    files_count: int
    chunks_count: int
    total_tokens: int
    last_indexed: str


class TokenCountResponse(BaseModel):
    """Token count result."""
    text: str
    token_count: int
    model: str


class SettingsResponse(BaseModel):
    """Exposed settings (no secrets)."""
    default_llm_provider: str
    embedding_provider: str
    default_token_budget: int
    max_token_budget: int
    min_token_budget: int
    supported_extensions: list[str]
    ollama_base_url: str
    eval_grounding_threshold: float
