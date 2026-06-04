"""Tests for Auto RAG routing (keyword + mocked scores)."""

from unittest.mock import patch

from terramind.models.router import route_question


def test_route_product_keywords_without_scores():
    with patch("terramind.models.router._probe_top_score", return_value=None):
        route, _ = route_question(
            "What is the label dosage and how do I apply this catalog product?",
            "dosage apply catalog product",
        )
    assert route == "product_rag"


def test_route_general_topics_without_scores():
    with patch("terramind.models.router._probe_top_score", return_value=None):
        route, _ = route_question(
            "What are integrated pest management steps before spraying?",
            "integrated pest management ipm",
        )
    assert route == "general_rag"


def test_route_catalog_score_wins():
    calls: list[int] = []

    def fake_probe(db, query):
        calls.append(1)
        return 0.55 if len(calls) == 1 else 0.75

    with patch("terramind.models.router._probe_top_score", side_effect=fake_probe):
        route, reason = route_question("Which fungicide should I use?", "fungicide")
    assert route == "product_rag"
    assert "stronger" in reason


def test_route_mixed_tied_goes_general():
    with patch("terramind.models.router._probe_top_score", return_value=0.5):
        route, reason = route_question(
            "Potato late blight — which product from our catalog helps?",
            "late blight catalog product",
        )
    assert route == "general_rag"
    assert "mixed" in reason.lower() or "guidance" in reason.lower()
