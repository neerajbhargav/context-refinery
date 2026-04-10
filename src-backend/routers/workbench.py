"""
ContextRefinery — Workbench Router

Endpoints for project management, file indexing, and token counting.
"""

from __future__ import annotations

import logging
from datetime import datetime

from fastapi import APIRouter, HTTPException

from models.schemas import (
    IndexRequest,
    IndexResponse,
    TokenCountRequest,
    TokenCountResponse,
    ProjectInfo,
)
from retriever.indexer import index_project, get_chroma_client, get_collection_name
from services.token_counter import count_tokens
from services.persistence import db
from config import settings
import uuid

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/workbench", tags=["workbench"])


@router.post("/index", response_model=IndexResponse)
async def index_project_folder(request: IndexRequest):
    """Index a project folder into ChromaDB for retrieval."""
    try:
        # Generate a unique ID if not provided (for first-time indexing)
        project_id = str(uuid.uuid5(uuid.NAMESPACE_URL, request.folder_path))
        
        result = await index_project(
            project_name=request.project_name,
            folder_path=request.folder_path,
            extensions=request.extensions,
        )
        
        # Persistence registry
        db.save_project(
            id=project_id,
            name=request.project_name,
            root_path=request.folder_path,
            collection_name=get_collection_name(request.project_name)
        )
        
        return IndexResponse(**result)
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Indexing error: {e}")
        raise HTTPException(status_code=500, detail=f"Indexing failed: {str(e)}")


@router.post("/count-tokens", response_model=TokenCountResponse)
async def count_text_tokens(request: TokenCountRequest):
    """Count tokens in the provided text for a given model."""
    token_count = count_tokens(request.text, request.model)
    return TokenCountResponse(
        text=request.text[:100] + "..." if len(request.text) > 100 else request.text,
        token_count=token_count,
        model=request.model,
    )


@router.get("/projects", response_model=list[ProjectInfo])
async def list_indexed_projects():
    """List all indexed projects from persistence registry."""
    project_rows = db.list_projects()
    
    # Enrich with ChromaDB counts
    client = get_chroma_client()
    projects = []
    
    for p in project_rows:
        try:
            collection = client.get_collection(p["collection_name"])
            count = collection.count()
        except Exception as e:
            logger.warning(f"Failed to get collection {p['collection_name']}: {e}")
            count = 0
            
        projects.append(ProjectInfo(
            name=p["name"],
            folder_path=p["root_path"],
            files_count=0, # Need deeper scan to implement
            chunks_count=count,
            total_tokens=0,
            last_indexed=p["last_indexed_at"] or p["created_at"],
        ))

    return projects


@router.delete("/projects/{project_name}")
async def delete_project(project_name: str):
    """Delete an indexed project."""
    client = get_chroma_client()
    collection_name = get_collection_name(project_name)
    try:
        client.delete_collection(collection_name)
        return {"status": "deleted", "project": project_name}
    except Exception as e:
        raise HTTPException(status_code=404, detail=f"Project not found: {str(e)}")
