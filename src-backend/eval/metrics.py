"""
ContextRefinery — Custom Evaluation Metrics

Lightweight, local-first metrics that don't require an external LLM.
These provide fast feedback for the refinement loop.
"""

from __future__ import annotations

import math
import re
from collections import Counter

from services.token_counter import count_tokens


def compute_context_grounding(
    prompt: str,
    context_chunks: list[str],
    ngram_size: int = 3,
) -> float:
    """
    Measure what fraction of the prompt content is grounded in the 
    source context chunks.
    
    Uses n-gram overlap between the prompt and context to estimate
    how much of the prompt can be traced back to source material.
    
    Returns: 0.0 to 1.0 (higher = better grounded)
    """
    if not prompt or not context_chunks:
        return 0.0

    def extract_ngrams(text: str, n: int) -> set[str]:
        words = re.findall(r'\w+', text.lower())
        return set(
            " ".join(words[i:i + n])
            for i in range(len(words) - n + 1)
        )

    prompt_ngrams = extract_ngrams(prompt, ngram_size)
    if not prompt_ngrams:
        return 0.0

    # Union of all context n-grams
    context_ngrams: set[str] = set()
    for chunk in context_chunks:
        context_ngrams.update(extract_ngrams(chunk, ngram_size))

    if not context_ngrams:
        return 0.0

    # Intersection / prompt n-grams
    overlap = prompt_ngrams & context_ngrams
    grounding_ratio = len(overlap) / len(prompt_ngrams)

    # Apply a sigmoid-like scaling to make scores more useful
    # Raw overlap tends to be low; scale so 30% overlap → 0.75 score
    scaled = 1.0 / (1.0 + math.exp(-10 * (grounding_ratio - 0.2)))

    return min(1.0, scaled)


def compute_information_density(prompt: str) -> float:
    """
    Measure the unique information per token in the prompt.
    
    Uses type-token ratio (TTR) and vocabulary richness as proxies
    for information density. A prompt with lots of repetition has
    low density; a prompt with diverse vocabulary has high density.
    
    Returns: 0.0 to 1.0 (higher = more information-dense)
    """
    if not prompt:
        return 0.0

    words = re.findall(r'\w+', prompt.lower())
    if len(words) < 5:
        return 0.5  # Too short to evaluate

    # Type-Token Ratio (TTR)
    unique_words = set(words)
    ttr = len(unique_words) / len(words)

    # Hapax legomena ratio (words appearing only once)
    word_counts = Counter(words)
    hapax = sum(1 for count in word_counts.values() if count == 1)
    hapax_ratio = hapax / len(words) if words else 0

    # Weighted combination
    density = (ttr * 0.6) + (hapax_ratio * 0.4)

    # Scale to a more useful range (raw TTR tends to be 0.3-0.6)
    scaled = min(1.0, density * 1.5)

    return scaled


def compute_budget_utilization(prompt: str, token_budget: int) -> float:
    """
    Measure how efficiently the token budget is utilized.
    
    Penalizes both under-utilization (wasted budget) and 
    over-utilization (exceeding budget).
    
    Returns: 0.0 to 1.0 (higher = better utilization)
    """
    if token_budget <= 0:
        return 0.0

    actual_tokens = count_tokens(prompt)
    ratio = actual_tokens / token_budget

    if ratio > 1.0:
        # Over budget — penalize exponentially
        return max(0.0, 1.0 - (ratio - 1.0) * 2)
    elif ratio < 0.3:
        # Severely under-utilized
        return ratio * 2
    elif ratio < 0.5:
        # Moderately under-utilized
        return 0.6 + (ratio - 0.3) * 2
    else:
        # Sweet spot: 50-100% utilization
        return 1.0 - (1.0 - ratio) * 0.2
