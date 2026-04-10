"""
ContextRefinery — ChromaDB Indexer

Handles ingestion of source files into ChromaDB with dual embeddings
(dense vectors for semantic search). BM25 scoring is handled separately
in the hybrid retriever.
"""

from __future__ import annotations

import hashlib
import logging
import os
from pathlib import Path

import chromadb
from chromadb.config import Settings as ChromaSettings

from config import settings
from models.state import SourceFile
from services.token_counter import count_tokens
from services.file_processor import process_file, chunk_text
from retriever.embeddings import get_embedding_function
import pickle

logger = logging.getLogger(__name__)

# Module-level ChromaDB client (initialized in main.py lifespan)
_chroma_client: chromadb.ClientAPI | None = None


def get_chroma_client() -> chromadb.ClientAPI:
    """Get or create the ChromaDB persistent client."""
    global _chroma_client
    if _chroma_client is None:
        _chroma_client = chromadb.PersistentClient(
            path=str(settings.CHROMA_PERSIST_DIR),
            settings=ChromaSettings(
                anonymized_telemetry=False,
                allow_reset=True,
            ),
        )
    return _chroma_client


def set_chroma_client(client: chromadb.ClientAPI) -> None:
    """Set the ChromaDB client (used during app lifespan setup)."""
    global _chroma_client
    _chroma_client = client


def get_collection_name(project_name: str) -> str:
    """Generate a ChromaDB collection name from a project name."""
    safe = project_name.lower().replace(" ", "_").replace("-", "_")
    return f"{settings.CHROMA_COLLECTION_PREFIX}{safe}"


async def index_project(
    project_name: str,
    folder_path: str,
    extensions: list[str] | None = None,
) -> dict:
    """
    Index all supported files in a project folder into ChromaDB.
    
    Returns stats about the indexing operation.
    """
    client = get_chroma_client()
    collection_name = get_collection_name(project_name)
    
    # Get or create collection (reset if exists for re-indexing)
    try:
        client.delete_collection(collection_name)
    except Exception:
        pass
    
    collection = client.get_or_create_collection(
        name=collection_name,
        metadata={"hnsw:space": "cosine"},
        embedding_function=get_embedding_function(),
    )

    allowed_extensions = set(extensions or settings.SUPPORTED_EXTENSIONS)
    folder = Path(folder_path)

    if not folder.exists():
        raise FileNotFoundError(f"Folder not found: {folder_path}")

    documents = []
    metadatas = []
    ids = []

    files_indexed = 0
    total_tokens = 0

    for file_path in folder.rglob("*"):
        if not file_path.is_file():
            continue
        if file_path.suffix.lower() not in allowed_extensions:
            continue
        # Skip hidden/build directories
        parts = file_path.relative_to(folder).parts
        if any(p.startswith(".") or p in ("node_modules", "__pycache__", "dist", "build", ".git") for p in parts):
            continue

        try:
            content, language = process_file(file_path)
            if not content.strip():
                continue

            chunks = chunk_text(
                content,
                chunk_size=settings.CHUNK_SIZE,
                chunk_overlap=settings.CHUNK_OVERLAP,
            )

            for i, chunk_text_content in enumerate(chunks):
                chunk_id = hashlib.md5(
                    f"{file_path}:{i}".encode()
                ).hexdigest()

                tokens = count_tokens(chunk_text_content)
                total_tokens += tokens

                documents.append(chunk_text_content)
                metadatas.append({
                    "source_file": str(file_path.relative_to(folder)),
                    "language": language,
                    "chunk_index": i,
                    "total_chunks": len(chunks),
                    "token_count": tokens,
                    "start_line": i * (settings.CHUNK_SIZE - settings.CHUNK_OVERLAP) + 1,
                    "end_line": min(
                        (i + 1) * settings.CHUNK_SIZE,
                        content.count("\n") + 1,
                    ),
                })
                ids.append(chunk_id)

            files_indexed += 1

        except Exception as e:
            logger.warning(f"Failed to process {file_path}: {e}")
            continue

    # Generate and save BM25 index
    if documents:
        # ChromaDB batch upsert
        batch_size = 100
        for i in range(0, len(documents), batch_size):
            collection.add(
                documents=documents[i:i + batch_size],
                metadatas=metadatas[i:i + batch_size],
                ids=ids[i:i + batch_size],
            )

        # BM25 Generation
        from rank_bm25 import BM25Okapi
        # Simple whitespace tokenization as a fallback for sparse indexing
        tokenized_docs = [doc.lower().split() for doc in documents]
        bm25 = BM25Okapi(tokenized_docs)
        
        # Save BM25 index
        bm25_path = Path(settings.CHROMA_PERSIST_DIR) / f"{collection_name}.bm25.pkl"
        with open(bm25_path, "wb") as f:
            pickle.dump(bm25, f)
            
        logger.info(f"BM25 index saved to {bm25_path}")

    logger.info(
        f"Indexed project '{project_name}': "
        f"{files_indexed} files, {len(documents)} chunks, {total_tokens} tokens"
    )

    return {
        "project_name": project_name,
        "files_indexed": files_indexed,
        "chunks_created": len(documents),
        "total_tokens": total_tokens,
    }


async def index_files(
    source_files: list[SourceFile],
    project_name: str = "_adhoc",
) -> str:
    """
    Index a list of SourceFile objects (from drag-and-drop) into ChromaDB.
    Returns the collection name.
    """
    client = get_chroma_client()
    collection_name = get_collection_name(project_name)

    collection = client.get_or_create_collection(
        name=collection_name,
        metadata={"hnsw:space": "cosine"},
        embedding_function=get_embedding_function(),
    )

    documents = []
    metadatas = []
    ids = []

    for sf in source_files:
        chunks = chunk_text(
            sf.content,
            chunk_size=settings.CHUNK_SIZE,
            chunk_overlap=settings.CHUNK_OVERLAP,
        )

        for i, chunk_content in enumerate(chunks):
            chunk_id = hashlib.md5(
                f"{sf.path}:{i}".encode()
            ).hexdigest()

            tokens = count_tokens(chunk_content)

            documents.append(chunk_content)
            metadatas.append({
                "source_file": sf.filename,
                "language": sf.language,
                "chunk_index": i,
                "total_chunks": len(chunks),
                "token_count": tokens,
                "start_line": i * (settings.CHUNK_SIZE - settings.CHUNK_OVERLAP) + 1,
                "end_line": min(
                    (i + 1) * settings.CHUNK_SIZE,
                    sf.content.count("\n") + 1,
                ),
            })
            ids.append(chunk_id)

            sf.chunk_ids.append(chunk_id)

    if documents:
        batch_size = 100
        for i in range(0, len(documents), batch_size):
            collection.add(
                documents=documents[i:i + batch_size],
                metadatas=metadatas[i:i + batch_size],
                ids=ids[i:i + batch_size],
            )
        
        # We don't save BM25 for ad-hoc D&D yet, 
        # or we could keep it in memory for the session.
        # For now, let's just make it available for the hybrid search.

    return collection_name
