"""
ContextRefinery — Cross-Encoder Reranker

Uses a cross-encoder model to rerank candidate chunks by their
relevance to the query. This is the precision stage of the retrieval
pipeline — it runs after the recall-optimized hybrid retrieval.
"""

from __future__ import annotations

import logging
from functools import lru_cache

from models.state import Chunk
from config import settings

logger = logging.getLogger(__name__)

# Lazy-loaded reranker model
_reranker = None


def _get_reranker():
    """Lazy-load the cross-encoder reranker model."""
    global _reranker
    if _reranker is None:
        try:
            from sentence_transformers import CrossEncoder
            _reranker = CrossEncoder(
                settings.RERANKER_MODEL,
                max_length=512,
            )
            logger.info(f"Loaded reranker model: {settings.RERANKER_MODEL}")
        except Exception as e:
            logger.warning(f"Could not load reranker model: {e}. Falling back to RRF scores.")
            _reranker = "UNAVAILABLE"
    return _reranker


async def rerank_chunks(
    query: str,
    chunks: list[Chunk],
) -> list[Chunk]:
    """
    Rerank chunks using a cross-encoder model.
    
    Takes (query, chunk) pairs and scores them for relevance.
    If the model is unavailable, falls back to RRF score ordering.
    
    Args:
        query: The search query
        chunks: Candidate chunks from hybrid retrieval
    
    Returns:
        Chunks sorted by reranker score (descending)
    """
    if not chunks:
        return []

    reranker = _get_reranker()

    if reranker == "UNAVAILABLE" or reranker is None:
        # Fallback: just use RRF scores
        logger.info("Using RRF fallback (no reranker available)")
        return sorted(chunks, key=lambda c: c.rrf_score, reverse=True)

    try:
        # Prepare (query, document) pairs for the cross-encoder
        pairs = [(query, chunk.content) for chunk in chunks]

        # Score all pairs
        scores = reranker.predict(pairs)

        # Assign rerank scores
        for chunk, score in zip(chunks, scores):
            chunk.rerank_score = float(score)

        # Sort by rerank score descending
        reranked = sorted(chunks, key=lambda c: c.rerank_score, reverse=True)

        logger.info(
            f"Reranked {len(chunks)} chunks. "
            f"Top score: {reranked[0].rerank_score:.4f}, "
            f"Bottom score: {reranked[-1].rerank_score:.4f}"
        )

        return reranked

    except Exception as e:
        logger.error(f"Reranking failed: {e}. Falling back to RRF scores.")
        return sorted(chunks, key=lambda c: c.rrf_score, reverse=True)
