"""
ContextRefinery — Centralized Configuration
Uses Pydantic BaseSettings for environment-driven config.
"""

from pathlib import Path
from pydantic_settings import BaseSettings
from pydantic import Field
from typing import Literal


class Settings(BaseSettings):
    """Application settings loaded from environment variables and .env file."""

    # ── Server ──────────────────────────────────────────────────────────
    SIDECAR_HOST: str = "127.0.0.1"
    SIDECAR_PORT: int = 8741
    CORS_ORIGINS: list[str] = ["*"]

    # ── LLM Provider ────────────────────────────────────────────────────
    DEFAULT_LLM_PROVIDER: Literal["openai", "anthropic", "google", "ollama"] = "google"
    OPENAI_API_KEY: str | None = None
    ANTHROPIC_API_KEY: str | None = None
    GOOGLE_API_KEY: str | None = None

    # Ollama (local fallback)
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "gemma3"

    # ── Embeddings ──────────────────────────────────────────────────────
    EMBEDDING_PROVIDER: Literal["google", "ollama", "sentence-transformers"] = "google"
    GOOGLE_EMBEDDING_MODEL: str = "models/text-embedding-004"
    OLLAMA_EMBEDDING_MODEL: str = "gemma3"
    LOCAL_EMBEDDING_MODEL: str = "all-MiniLM-L6-v2"

    # ── Reranker ────────────────────────────────────────────────────────
    RERANKER_MODEL: str = "cross-encoder/ms-marco-MiniLM-L-6-v2"
    RERANKER_TOP_K: int = 10

    # ── Retrieval ───────────────────────────────────────────────────────
    HYBRID_RETRIEVAL_K: int = 50  # Over-fetch for reranker
    RRF_K: int = 60  # Reciprocal Rank Fusion constant
    DEFAULT_TOKEN_BUDGET: int = 4096
    MAX_TOKEN_BUDGET: int = 32768
    MIN_TOKEN_BUDGET: int = 512

    # ── ChromaDB ────────────────────────────────────────────────────────
    CHROMA_PERSIST_DIR: Path = Path.home() / ".context-refinery" / "chroma"
    CHROMA_COLLECTION_PREFIX: str = "cr_project_"

    # ── Chunking ────────────────────────────────────────────────────────
    CHUNK_SIZE: int = 512
    CHUNK_OVERLAP: int = 64
    SUPPORTED_EXTENSIONS: list[str] = [
        ".py", ".js", ".ts", ".jsx", ".tsx", ".vue", ".rs",
        ".go", ".java", ".cpp", ".c", ".h", ".hpp",
        ".md", ".txt", ".json", ".yaml", ".yml", ".toml",
        ".html", ".css", ".scss", ".sql", ".sh", ".ps1",
        ".rb", ".php", ".swift", ".kt",
    ]

    # ── Eval ────────────────────────────────────────────────────────────
    EVAL_GROUNDING_THRESHOLD: float = 0.75
    EVAL_MAX_ITERATIONS: int = 3

    # ── Storage ─────────────────────────────────────────────────────────
    DATA_DIR: Path = Path.home() / ".context-refinery"
    PROJECTS_DIR: Path = Path.home() / ".context-refinery" / "projects"

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "case_sensitive": True,
    }


# Singleton
settings = Settings()

# Ensure directories exist
settings.DATA_DIR.mkdir(parents=True, exist_ok=True)
settings.PROJECTS_DIR.mkdir(parents=True, exist_ok=True)
settings.CHROMA_PERSIST_DIR.mkdir(parents=True, exist_ok=True)
