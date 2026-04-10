"""
ContextRefinery — Setup Router
First-run configuration: detect Ollama, test LLM connections, save .env config.
"""

import os
import logging
from pathlib import Path
from typing import Optional

import httpx
from fastapi import APIRouter
from pydantic import BaseModel

from config import settings

router = APIRouter(prefix="/api/setup", tags=["setup"])
logger = logging.getLogger(__name__)

ENV_PATH = Path(__file__).parent.parent / ".env"
SETUP_MARKER = settings.DATA_DIR / ".setup_complete"


class SetupStatus(BaseModel):
    setup_complete: bool
    ollama_running: bool = False
    ollama_models: list[str] = []
    current_provider: str = ""


class TestConnectionRequest(BaseModel):
    provider: str  # "ollama" | "google" | "openai" | "anthropic"
    api_key: Optional[str] = None
    ollama_model: Optional[str] = None


class SaveConfigRequest(BaseModel):
    provider: str
    api_key: Optional[str] = None
    ollama_model: Optional[str] = None
    embedding_provider: str = "sentence-transformers"


@router.get("/status")
async def get_setup_status() -> SetupStatus:
    """Check if first-run setup has been completed and detect Ollama."""
    ollama_running = False
    ollama_models = []

    try:
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                f"{settings.OLLAMA_BASE_URL}/api/tags", timeout=3.0
            )
            if resp.status_code == 200:
                ollama_running = True
                data = resp.json()
                ollama_models = [
                    m["name"] for m in data.get("models", [])
                ]
    except Exception:
        pass

    return SetupStatus(
        setup_complete=SETUP_MARKER.exists(),
        ollama_running=ollama_running,
        ollama_models=ollama_models,
        current_provider=settings.DEFAULT_LLM_PROVIDER,
    )


@router.post("/test-connection")
async def test_connection(req: TestConnectionRequest):
    """Test that the selected LLM provider is reachable."""
    try:
        if req.provider == "ollama":
            async with httpx.AsyncClient() as client:
                resp = await client.get(
                    f"{settings.OLLAMA_BASE_URL}/api/tags", timeout=5.0
                )
                if resp.status_code != 200:
                    return {"success": False, "error": "Ollama is not responding"}
                models = [m["name"] for m in resp.json().get("models", [])]
                if req.ollama_model and req.ollama_model not in models:
                    return {
                        "success": False,
                        "error": f"Model '{req.ollama_model}' not found. Available: {', '.join(models[:5])}",
                    }
                return {"success": True, "message": "Ollama is running"}

        elif req.provider == "google":
            if not req.api_key:
                return {"success": False, "error": "Google API key is required"}
            async with httpx.AsyncClient() as client:
                resp = await client.get(
                    "https://generativelanguage.googleapis.com/v1beta/models",
                    params={"key": req.api_key},
                    timeout=10.0,
                )
                if resp.status_code == 200:
                    return {"success": True, "message": "Google API key is valid"}
                return {"success": False, "error": f"Google API returned {resp.status_code}"}

        elif req.provider == "openai":
            if not req.api_key:
                return {"success": False, "error": "OpenAI API key is required"}
            async with httpx.AsyncClient() as client:
                resp = await client.get(
                    "https://api.openai.com/v1/models",
                    headers={"Authorization": f"Bearer {req.api_key}"},
                    timeout=10.0,
                )
                if resp.status_code == 200:
                    return {"success": True, "message": "OpenAI API key is valid"}
                return {"success": False, "error": f"OpenAI API returned {resp.status_code}"}

        elif req.provider == "anthropic":
            if not req.api_key:
                return {"success": False, "error": "Anthropic API key is required"}
            # Anthropic doesn't have a /models list; we just validate the key format
            if req.api_key.startswith("sk-ant-"):
                return {"success": True, "message": "Anthropic API key format is valid"}
            return {"success": False, "error": "Anthropic API key should start with 'sk-ant-'"}

        return {"success": False, "error": f"Unknown provider: {req.provider}"}

    except Exception as e:
        return {"success": False, "error": str(e)}


@router.post("/save-config")
async def save_config(req: SaveConfigRequest):
    """Write the selected configuration to .env and mark setup as complete."""
    try:
        lines = [
            "# ContextRefinery — Auto-generated configuration",
            f"DEFAULT_LLM_PROVIDER={req.provider}",
            "",
        ]

        if req.provider == "google" and req.api_key:
            lines.append(f"GOOGLE_API_KEY={req.api_key}")
        elif req.provider == "openai" and req.api_key:
            lines.append(f"OPENAI_API_KEY={req.api_key}")
        elif req.provider == "anthropic" and req.api_key:
            lines.append(f"ANTHROPIC_API_KEY={req.api_key}")
        elif req.provider == "ollama":
            lines.append(f"OLLAMA_MODEL={req.ollama_model or 'gemma3'}")
            lines.append(f"OLLAMA_BASE_URL={settings.OLLAMA_BASE_URL}")

        lines.extend([
            "",
            f"EMBEDDING_PROVIDER={req.embedding_provider}",
            f"SIDECAR_PORT={settings.SIDECAR_PORT}",
        ])

        ENV_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")

        # Mark setup as complete
        SETUP_MARKER.parent.mkdir(parents=True, exist_ok=True)
        SETUP_MARKER.write_text("1")

        logger.info(f"Setup saved: provider={req.provider}, embedding={req.embedding_provider}")
        return {"success": True, "message": "Configuration saved. Restart the backend to apply."}

    except Exception as e:
        logger.error(f"Failed to save config: {e}")
        return {"success": False, "error": str(e)}
