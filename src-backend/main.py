"""
ContextRefinery — FastAPI Sidecar Application

The AI backend for ContextRefinery. Runs as a PyInstaller-bundled sidecar
process alongside the Tauri desktop shell.

Provides:
  - SSE streaming endpoint for real-time prompt refinement
  - REST endpoints for project indexing, eval, and settings
  - LangGraph-powered multi-agent orchestration
  - Hybrid retrieval with ChromaDB + BM25 + cross-encoder reranking
"""

from __future__ import annotations

import sys
import logging
import argparse
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from config import settings

# ── Logging Setup ──────────────────────────────────────────────────────

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s │ %(name)-25s │ %(levelname)-7s │ %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("context-refinery")

# ── LLM Provider Factory ──────────────────────────────────────────────

_llm_instance = None


def get_llm():
    """
    Get the configured LLM instance.
    
    Supports: OpenAI, Anthropic, Google (Gemini), Ollama (local).
    The provider is determined by settings.DEFAULT_LLM_PROVIDER.
    """
    global _llm_instance
    if _llm_instance is not None:
        return _llm_instance

    provider = settings.DEFAULT_LLM_PROVIDER

    if provider == "openai":
        from langchain_openai import ChatOpenAI
        _llm_instance = ChatOpenAI(
            model="gpt-4o",
            api_key=settings.OPENAI_API_KEY,
            temperature=0.3,
        )

    elif provider == "anthropic":
        from langchain_anthropic import ChatAnthropic
        _llm_instance = ChatAnthropic(
            model="claude-sonnet-4-20250514",
            api_key=settings.ANTHROPIC_API_KEY,
            temperature=0.3,
        )

    elif provider == "google":
        from langchain_google_genai import ChatGoogleGenerativeAI
        _llm_instance = ChatGoogleGenerativeAI(
            model="gemini-2.5-pro-preview-05-06",
            google_api_key=settings.GOOGLE_API_KEY,
            temperature=0.3,
        )

    elif provider == "ollama":
        from langchain_ollama import ChatOllama
        _llm_instance = ChatOllama(
            model=settings.OLLAMA_MODEL,
            base_url=settings.OLLAMA_BASE_URL,
            temperature=0.3,
        )

    else:
        raise ValueError(f"Unknown LLM provider: {provider}")

    logger.info(f"Initialized LLM provider: {provider}")
    return _llm_instance


# ── Application Lifespan ───────────────────────────────────────────────


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager.
    
    Startup:
      - Initialize ChromaDB client
      - Warm up LLM provider
      - Pre-compile LangGraph
    
    Shutdown:
      - Cleanup resources
    """
    logger.info("=" * 60)
    logger.info("  ContextRefinery Sidecar Starting")
    logger.info(f"  Port: {settings.SIDECAR_PORT}")
    logger.info(f"  LLM Provider: {settings.DEFAULT_LLM_PROVIDER}")
    logger.info(f"  Embedding Provider: {settings.EMBEDDING_PROVIDER}")
    logger.info(f"  ChromaDB: {settings.CHROMA_PERSIST_DIR}")
    logger.info("=" * 60)

    # Initialize ChromaDB
    from retriever.indexer import get_chroma_client
    client = get_chroma_client()
    logger.info(f"ChromaDB initialized with {len(client.list_collections())} existing collections")

    # Pre-compile LangGraph
    from agents.graph import build_refinery_graph
    graph = build_refinery_graph()
    logger.info("LangGraph pipeline compiled")

    yield

    # Cleanup
    logger.info("ContextRefinery Sidecar shutting down")


# ── FastAPI Application ────────────────────────────────────────────────

app = FastAPI(
    title="ContextRefinery API",
    description="Context Orchestration Engine — AI-powered prompt refinement sidecar",
    version="0.1.0",
    lifespan=lifespan,
)

# CORS for Tauri webview
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Register Routers ──────────────────────────────────────────────────

from routers import refinery, workbench, eval, models, setup

# ── Routers ─────────────────────────────────────────────────────────
app.include_router(workbench.router)
app.include_router(refinery.router)
app.include_router(eval.router)
app.include_router(models.router)
app.include_router(setup.router)


# ── Health Check ───────────────────────────────────────────────────────


@app.get("/api/health")
async def health_check():
    """Health check endpoint for Tauri sidecar monitoring."""
    from models.schemas import HealthResponse
    return HealthResponse(
        status="ok",
        version="0.1.0",
        llm_provider=settings.DEFAULT_LLM_PROVIDER,
        embedding_provider=settings.EMBEDDING_PROVIDER,
    )


@app.get("/api/settings")
async def get_settings():
    """Get exposed application settings (no secrets)."""
    from models.schemas import SettingsResponse
    return SettingsResponse(
        default_llm_provider=settings.DEFAULT_LLM_PROVIDER,
        embedding_provider=settings.EMBEDDING_PROVIDER,
        default_token_budget=settings.DEFAULT_TOKEN_BUDGET,
        max_token_budget=settings.MAX_TOKEN_BUDGET,
        min_token_budget=settings.MIN_TOKEN_BUDGET,
        supported_extensions=settings.SUPPORTED_EXTENSIONS,
        ollama_base_url=settings.OLLAMA_BASE_URL,
        eval_grounding_threshold=settings.EVAL_GROUNDING_THRESHOLD,
    )


# ── Entry Point ────────────────────────────────────────────────────────

if __name__ == "__main__":
    import uvicorn

    parser = argparse.ArgumentParser(description="ContextRefinery Sidecar")
    parser.add_argument("--port", type=int, default=settings.SIDECAR_PORT)
    parser.add_argument("--host", type=str, default=settings.SIDECAR_HOST)
    args = parser.parse_args()

    uvicorn.run(
        "main:app",
        host=args.host,
        port=args.port,
        reload=False,
        log_level="info",
    )
