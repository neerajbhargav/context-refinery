"""
ContextRefinery — Hybrid Retriever

Combines dense vector search (ChromaDB) with BM25 lexical search,
fuses results using Reciprocal Rank Fusion (RRF), then applies
cross-encoder reranking to select the best chunks within the token budget.
"""

from __future__ import annotations

import logging
import math

from rank_bm25 import BM25Okapi

from config import settings
from models.state import SourceFile, Chunk
from services.token_counter import count_tokens
from services.file_processor import chunk_text
from retriever.indexer import get_chroma_client, index_files, get_collection_name
from retriever.reranker import rerank_chunks
import os
import pickle
from pathlib import Path

logger = logging.getLogger(__name__)


def _reciprocal_rank_fusion(
    rankings: list[list[tuple[str, float]]],
    k: int = 60,
) -> dict[str, float]:
    """
    Reciprocal Rank Fusion (RRF) to merge multiple ranked lists.
    
    Args:
        rankings: List of ranked lists, each containing (doc_id, score) tuples
        k: RRF constant (default 60)
    
    Returns:
        Dict of doc_id → fused score
    """
    fused_scores: dict[str, float] = {}

    for ranking in rankings:
        for rank, (doc_id, _score) in enumerate(ranking):
            if doc_id not in fused_scores:
                fused_scores[doc_id] = 0.0
            fused_scores[doc_id] += 1.0 / (k + rank + 1)

    return fused_scores


async def hybrid_retrieve(
    query: str,
    source_files: list[SourceFile],
    token_budget: int,
    top_k: int = 10,
    project_name: str = "_adhoc",
) -> list[Chunk]:
    """
    Perform hybrid retrieval combining dense + BM25 search.
    
    Pipeline:
      1. Index files into ChromaDB (if not already indexed)
      2. Dense retrieval via ChromaDB
      3. BM25 retrieval on raw text
      4. RRF fusion of both rankings
      5. Cross-encoder reranking
      6. Token budget truncation (greedy knapsack)
    
    Args:
        query: The search query (goal + key concepts)
        source_files: List of source files to search over
        token_budget: Maximum total tokens for selected chunks
        top_k: Number of final chunks to return after reranking
        project_name: ChromaDB collection prefix
    
    Returns:
        List of ranked Chunk objects fitting within token_budget
    """
    if not source_files:
        logger.warning("No source files provided for retrieval")
        return []

    # ── Step 1: Ensure files are indexed ────────────────────────────
    collection_name = await index_files(source_files, project_name)
    client = get_chroma_client()
    collection = client.get_collection(collection_name)

    # ── Step 2: Dense retrieval via ChromaDB ────────────────────────
    n_results = min(settings.HYBRID_RETRIEVAL_K * 2, collection.count())
    if n_results == 0:
        return []

    dense_results = collection.query(
        query_texts=[query],
        n_results=n_results,
        include=["documents", "metadatas", "distances"],
    )

    doc_map: dict[str, dict] = {}
    dense_ranking: list[tuple[str, float]] = []

    if dense_results["ids"] and dense_results["ids"][0]:
        for i, doc_id in enumerate(dense_results["ids"][0]):
            distance = dense_results["distances"][0][i] if dense_results["distances"] else 1.0
            score = 1.0 - distance  # similarity

            doc_map[doc_id] = {
                "content": dense_results["documents"][0][i],
                "metadata": dense_results["metadatas"][0][i] or {},
                "dense_score": score,
            }
            dense_ranking.append((doc_id, score))

    # ── Step 3: Sparse retrieval via BM25 ───────────────────────────
    bm25_ranking: list[tuple[str, float]] = []
    bm25_path = Path(settings.CHROMA_PERSIST_DIR) / f"{collection_name}.bm25.pkl"

    bm25 = None
    if bm25_path.exists():
        try:
            with open(bm25_path, "rb") as f:
                bm25 = pickle.load(f)
        except Exception as e:
            logger.warning(f"Failed to load BM25 index at {bm25_path}: {e}")

    # If no persisted index (e.g. ad-hoc), build one in-memory
    if bm25 is None:
        all_docs = collection.get(include=["documents"])
        if all_docs["ids"]:
            from rank_bm25 import BM25Okapi
            tokenized_docs = [doc.lower().split() for doc in all_docs["documents"]]
            bm25 = BM25Okapi(tokenized_docs)
            # Map index back to IDs
            bm25_ids = all_docs["ids"]
            
            tokenized_query = query.lower().split()
            bm25_scores = bm25.get_scores(tokenized_query)
            bm25_ranking = sorted(
                zip(bm25_ids, bm25_scores),
                key=lambda x: x[1],
                reverse=True,
            )
    else:
        # Load all IDs from collection to map BM25 index
        # Note: This assumes the BM25 index order matches collection.get() order at creation time
        # For a truly robust system, we'd store the ID mapping in the pickle
        all_docs = collection.get(include=["ids", "documents"])
        if all_docs["ids"]:
            tokenized_query = query.lower().split()
            bm25_scores = bm25.get_scores(tokenized_query)
            bm25_ranking = sorted(
                zip(all_docs["ids"], bm25_scores),
                key=lambda x: x[1],
                reverse=True,
            )

    # ── Step 4: Merge results and fetch missing content ─────────────
    # Standard RRF takes top K from each. We'll take top retrievals.
    top_bm25 = bm25_ranking[:settings.HYBRID_RETRIEVAL_K]
    
    # Fetch content for BM25 results not in doc_map (dense results)
    missing_ids = [did for did, _ in top_bm25 if did not in doc_map]
    if missing_ids:
        missing_docs = collection.get(ids=missing_ids, include=["documents", "metadatas"])
        for i, doc_id in enumerate(missing_docs["ids"]):
            doc_map[doc_id] = {
                "content": missing_docs["documents"][i],
                "metadata": missing_docs["metadatas"][i] or {},
                "dense_score": 0.0, # Not found in dense top-k
            }

    # Populate scores for RRF
    for did, score in top_bm25:
        if did in doc_map:
            doc_map[did]["bm25_score"] = score

    # ── Step 5: RRF Fusion ──────────────────────────────────────────
    fused_scores = _reciprocal_rank_fusion(
        [dense_ranking, top_bm25],
        k=settings.RRF_K,
    )

    # Sort by fused score
    fused_ranking = sorted(
        fused_scores.items(),
        key=lambda x: x[1],
        reverse=True,
    )

    # Store RRF scores
    for doc_id, score in fused_ranking:
        if doc_id in doc_map:
            doc_map[doc_id]["rrf_score"] = score

    # Take top candidates for reranking
    candidates = []
    for doc_id, rrf_score in fused_ranking[:settings.HYBRID_RETRIEVAL_K]:
        if doc_id not in doc_map:
            continue
        info = doc_map[doc_id]
        meta = info.get("metadata", {})

        candidates.append(Chunk(
            id=doc_id,
            content=info["content"],
            source_file=meta.get("source_file", "unknown"),
            start_line=meta.get("start_line", 0),
            end_line=meta.get("end_line", 0),
            token_count=meta.get("token_count", count_tokens(info["content"])),
            dense_score=info.get("dense_score", 0.0),
            bm25_score=info.get("bm25_score", 0.0),
            rrf_score=rrf_score,
        ))

    # ── Step 6: Cross-encoder reranking ─────────────────────────────
    reranked = await rerank_chunks(query, candidates)

    # ── Step 6: Token budget truncation (greedy knapsack) ───────────
    # Reserve ~30% of budget for the prompt template itself
    context_budget = int(token_budget * 0.7)
    selected: list[Chunk] = []
    used_tokens = 0

    for chunk in reranked:
        if used_tokens + chunk.token_count <= context_budget:
            selected.append(chunk)
            used_tokens += chunk.token_count
        if len(selected) >= top_k:
            break

    logger.info(
        f"Hybrid retrieval: {len(candidates)} candidates → "
        f"{len(selected)} selected ({used_tokens}/{context_budget} context tokens)"
    )

    return selected
