"""
Improved version of similarity_score in metrics.py
========================================================
Idea: the old metric compares full text to full text, which penalizes
correct-but-long answers for their length. The new version measures
"golden content coverage" (semantic recall): for each sentence in the
golden answer, is its meaning present somewhere in the generated
answer? Extra additions in the generated answer are not penalized here
(that's left to Metric 2, which already owns that concern).

Signature and outputs are identical, no need to modify any runner.
"""
import re
import numpy as np
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity

# Same model currently in use — no change
model = SentenceTransformer("all-MiniLM-L6-v2")

# Control knob: 1.0 = recall only (gives the highest scores)
# For stricter scoring, lower it (e.g. 0.85) to blend in full-text
# similarity. Start with 1.0.
RECALL_WEIGHT = 1.0


def _split_sentences(text: str):
    """Split text into short sentences/claims, stripping Markdown headings and numbering."""
    text = re.sub(r'#+\s*', ' ', text)            # ### headings
    text = re.sub(r'\*\*', '', text)               # **bold**
    text = re.sub(r'^\s*\d+\.\s*', ' ', text, flags=re.M)  # 1. numbering
    text = re.sub(r'^\s*[-•]\s*', ' ', text, flags=re.M)   # bullet points
    parts = re.split(r'(?<=[.!?])\s+|\n+', text)
    return [p.strip() for p in parts if len(p.strip()) > 12]


def _recall_coverage(golden: str, generated: str) -> float:
    """
    For each golden sentence: max similarity to the closest sentence in
    the generated answer. The mean = golden content coverage ratio.
    """
    g_claims = _split_sentences(golden)
    p_claims = _split_sentences(generated)

    # edge case: text too short to split -> fall back to full-text similarity
    if not g_claims or not p_claims:
        e1, e2 = model.encode(golden), model.encode(generated)
        return float(cosine_similarity([e1], [e2])[0][0])

    g_emb = model.encode(g_claims)
    p_emb = model.encode(p_claims)
    sim = cosine_similarity(g_emb, p_emb)   # matrix (golden x generated)
    best_per_golden = sim.max(axis=1)        # best match per golden sentence
    return float(best_per_golden.mean())


def similarity_score(golden: str, generated: str) -> float:
    """
    Drop-in replacement for the old function (same signature and outputs).
    Defaults to recall only. If RECALL_WEIGHT < 1, blends in full-text similarity.
    """
    recall = _recall_coverage(golden, generated)

    if RECALL_WEIGHT >= 1.0:
        return recall

    e1, e2 = model.encode(golden), model.encode(generated)
    full = float(cosine_similarity([e1], [e2])[0][0])
    return RECALL_WEIGHT * recall + (1 - RECALL_WEIGHT) * full
