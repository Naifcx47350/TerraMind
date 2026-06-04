"""Tests for terramind.rag.scoring."""

from langchain_core.documents import Document

from terramind.rag.scoring import (
    aggregate_retrieval_score,
    confidence_from_retrieval,
    distance_to_relevance,
    sources_from_retrieved,
)


def test_distance_to_relevance_monotonic():
    assert distance_to_relevance(0.0) == 1.0
    assert distance_to_relevance(1.0) == 0.5
    assert distance_to_relevance(4.0) < distance_to_relevance(1.0)


def test_confidence_from_retrieval_bands():
    high = [Document(page_content="x", metadata={"relevance_score": 0.7})]
    low = [Document(page_content="x", metadata={"relevance_score": 0.2})]
    assert confidence_from_retrieval(high) == "high"
    assert confidence_from_retrieval(low) == "low"
    assert confidence_from_retrieval([]) == "low"


def test_sources_from_retrieved_dedupes_best_score():
    docs = [
        Document(
            page_content="a",
            metadata={"filename": "a.pdf", "source": "data/raw/documents/a.pdf"},
        ),
        Document(
            page_content="b",
            metadata={"filename": "a.pdf", "source": "data/raw/documents/a.pdf", "relevance_score": 0.9},
        ),
    ]
    sources = sources_from_retrieved("general", docs)
    assert len(sources) == 1
    assert sources[0]["relevance_score"] == 0.9
    assert sources[0]["chunk_count"] == 2


def test_aggregate_retrieval_score_max():
    docs = [
        Document(page_content="a", metadata={"relevance_score": 0.4}),
        Document(page_content="b", metadata={"relevance_score": 0.8}),
    ]
    assert aggregate_retrieval_score(docs) == 0.8
