"""
ContextRefinery — Model Management Router
Handles listing, pulling, and managing local models (Ollama).
"""

import json
import logging
import asyncio
import httpx
from fastapi import APIRouter, HTTPException, BackgroundTasks
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import List, Optional

from config import settings

router = APIRouter(prefix="/api/models", tags=["models"])
logger = logging.getLogger(__name__)

class PullRequest(BaseModel):
    model_name: str

@router.get("/ollama/tags")
async def list_ollama_models():
    """List all models currently available in local Ollama instance."""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{settings.OLLAMA_BASE_URL}/api/tags", timeout=5.0)
            if response.status_code != 200:
                return {"models": [], "status": "offline", "error": f"Ollama returned {response.status_code}"}
            
            data = response.json()
            return {"models": data.get("models", []), "status": "online"}
    except Exception as e:
        logger.warning(f"Could not connect to Ollama: {e}")
        return {"models": [], "status": "offline", "error": str(e)}

@router.post("/ollama/pull")
async def pull_ollama_model(req: PullRequest):
    """
    Stream model pull progress from Ollama to the client via SSE.
    """
    async def event_generator():
        try:
            async with httpx.AsyncClient() as client:
                async with client.stream(
                    "POST", 
                    f"{settings.OLLAMA_BASE_URL}/api/pull",
                    json={"name": req.model_name},
                    timeout=None
                ) as response:
                    
                    if response.status_code != 200:
                        yield f"data: {json.dumps({'event_type': 'error', 'data': {'error': f'Ollama pull failed with {response.status_code}'}})}\n\n"
                        return

                    async for line in response.aiter_lines():
                        if not line:
                            continue
                        
                        try:
                            # Ollama returns multiple JSON objects in one stream
                            data = json.loads(line)
                            
                            # Standardize for our frontend
                            progress_msg = {
                                "event_type": "progress",
                                "data": {
                                    "status": data.get("status"),
                                    "completed": data.get("completed"),
                                    "total": data.get("total"),
                                    "digest": data.get("digest")
                                }
                            }
                            yield f"data: {json.dumps(progress_msg)}\n\n"
                            
                        except json.JSONDecodeError:
                            continue

                    yield f"data: {json.dumps({'event_type': 'done', 'data': {'status': 'complete'}})}\n\n"

        except Exception as e:
            logger.error(f"Error during Ollama pull: {e}")
            yield f"data: {json.dumps({'event_type': 'error', 'data': {'error': str(e)}})}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")

@router.delete("/ollama/{model_name}")
async def delete_ollama_model(model_name: str):
    """Delete a model from local Ollama instance."""
    try:
        async with httpx.AsyncClient() as client:
            # Note: HTTPX DELETE with body isn't standard in all versions, 
            # but Ollama /api/delete expects {"name": "..."}
            response = await client.request(
                "DELETE",
                f"{settings.OLLAMA_BASE_URL}/api/delete",
                json={"name": model_name}
            )
            if response.status_code != 200:
                raise HTTPException(status_code=response.status_code, detail="Failed to delete model")
            return {"status": "deleted"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
