"""
ContextRefinery — Model-Aware Token Counter

Provides accurate token counting for different LLM tokenizers.
Uses tiktoken for OpenAI models, with estimation fallbacks for
Claude and Gemini models.
"""

from __future__ import annotations

import logging
from functools import lru_cache

logger = logging.getLogger(__name__)

# Lazy-loaded tokenizer
_tokenizer = None


def _get_tokenizer():
    """Get the tiktoken tokenizer (cl100k_base for GPT-4 family)."""
    global _tokenizer
    if _tokenizer is None:
        try:
            import tiktoken
            _tokenizer = tiktoken.get_encoding("cl100k_base")
            logger.info("Loaded tiktoken cl100k_base tokenizer")
        except ImportError:
            logger.warning("tiktoken not available, using word-based estimation")
            _tokenizer = "WORD_FALLBACK"
    return _tokenizer


def count_tokens(text: str, model: str = "gpt-4o") -> int:
    """
    Count tokens in text for the specified model.
    
    Uses tiktoken for OpenAI models. For Claude and Gemini,
    applies a scaling factor to the tiktoken count since their
    tokenizers are similar in density.
    
    Args:
        text: The text to count tokens for
        model: Target model identifier
    
    Returns:
        Estimated token count
    """
    if not text:
        return 0

    tokenizer = _get_tokenizer()

    if tokenizer == "WORD_FALLBACK":
        # Rough estimate: ~1.3 tokens per word
        return int(len(text.split()) * 1.3)

    base_count = len(tokenizer.encode(text))

    # Apply model-specific scaling factors
    # These are empirical approximations
    model_lower = model.lower()

    if "claude" in model_lower:
        # Claude's tokenizer is slightly more efficient
        return int(base_count * 0.95)
    elif "gemini" in model_lower:
        # Gemini's tokenizer is roughly similar
        return int(base_count * 1.0)
    elif "ollama" in model_lower or "gemma" in model_lower:
        # Local models vary, use conservative estimate
        return int(base_count * 1.05)
    else:
        # Default: OpenAI-compatible
        return base_count


def count_tokens_batch(texts: list[str], model: str = "gpt-4o") -> list[int]:
    """Count tokens for a batch of texts."""
    return [count_tokens(text, model) for text in texts]


def estimate_prompt_tokens(
    system_prompt: str,
    user_prompt: str,
    model: str = "gpt-4o",
) -> int:
    """
    Estimate the total token count for a system + user prompt pair,
    including message formatting overhead.
    """
    overhead = 10  # Message formatting tokens
    return (
        count_tokens(system_prompt, model) +
        count_tokens(user_prompt, model) +
        overhead
    )
