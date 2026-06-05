"""Query–chunk relevance scores and confidence for RAG responses."""

from __future__ import annotations

from typing import Literal

from langchain_core.documents import Document

from terramind.rag.source_display import dedupe_key, source_entry_from_chunk

PipelineKind = Literal["general", "product"]

# Chroma returns L2 distance (lower = closer). Map to (0, 1], higher = better match.
# Bands tuned for typical embedding distances (~0.5–2.0 → relevance ~0.67–0.33).
CONFIDENCE_HIGH = 0.52
CONFIDENCE_MEDIUM = 0.38


def distance_to_relevance(distance: float) -> float:
    d = max(0.0, float(distance))
    return 1.0 / (1.0 + d)


def chunk_relevance(doc: Document) -> float | None:
    raw = doc.metadata.get("relevance_score")
    if raw is None:
        return None
    try:
        return float(raw)
    except (TypeError, ValueError):
        return None


def aggregate_retrieval_score(retrieved: list[Document]) -> float | None:
    scores = [s for s in (chunk_relevance(d) for d in retrieved) if s is not None]
    return max(scores) if scores else None


def confidence_from_retrieval(retrieved: list[Document]) -> str:
    if not retrieved:
        return "low"
    score = aggregate_retrieval_score(retrieved)
    if score is None:
        return "low"
    if score >= CONFIDENCE_HIGH:
        return "high"
    if score >= CONFIDENCE_MEDIUM:
        return "medium"
    return "low"


def confidence_from_score(score: float | None, *, has_chunks: bool = True) -> str:
    """Advisory / merged paths when only an aggregate score is available."""
    if not has_chunks:
        return "low"
    if score is None:
        return "low"
    if score >= CONFIDENCE_HIGH:
        return "high"
    if score >= CONFIDENCE_MEDIUM:
        return "medium"
    return "low"


def sources_from_retrieved(
    pipeline: PipelineKind,
    retrieved: list[Document],
) -> list[dict]:
    """UI source chips with best relevance_score and chunk_count per dedupe key."""
    by_key: dict[str, dict] = {}

    for doc in retrieved:
        key = dedupe_key(pipeline, doc.metadata)
        score = chunk_relevance(doc)
        section = (
            doc.metadata.get("h3")
            or doc.metadata.get("h2")
            or doc.metadata.get("h1")
        )
        if key not in by_key:
            entry = source_entry_from_chunk(
                pipeline, doc.metadata, section=section
            )
            by_key[key] = {
                "entry": entry,
                "best": score,
                "count": 1,
            }
        else:
            row = by_key[key]
            row["count"] += 1
            if score is not None and (row["best"] is None or score > row["best"]):
                row["best"] = score

    out: list[dict] = []
    for row in by_key.values():
        entry = dict(row["entry"])
        if row["best"] is not None:
            entry["relevance_score"] = round(row["best"], 4)
        entry["chunk_count"] = row["count"]
        out.append(entry)
    return out


def rag_metrics(retrieved: list[Document], sources: list[dict]) -> dict:
    """Fields to merge into model answer dicts."""
    return {
        "sources": sources,
        "confidence": confidence_from_retrieval(retrieved),
        "retrieval_score": aggregate_retrieval_score(retrieved),
        "retrieved_chunks": len(retrieved),
    }
