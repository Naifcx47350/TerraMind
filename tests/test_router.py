"""Tests for Auto RAG routing (keyword + mocked scores)."""

from unittest.mock import patch

from core.models.router import route_question


def test_route_product_keywords_without_scores():
    with patch("core.models.router._probe_top_score", return_value=None):
        route, _ = route_question(
            "What is the label dosage and how do I apply this catalog product?",
            "dosage apply catalog product",
        )
    assert route == "product_rag"


def test_route_general_topics_without_scores():
    with patch("core.models.router._probe_top_score", return_value=None):
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

    with patch("core.models.router._probe_top_score", side_effect=fake_probe):
        route, reason = route_question("Which fungicide should I use?", "fungicide")
    assert route == "product_rag"
    assert "stronger" in reason


def test_route_mixed_catalog_ask_goes_product():
    with patch("core.models.router._probe_top_score", return_value=0.5):
        route, reason = route_question(
            "Potato late blight — which product from our catalog helps?",
            "late blight catalog product",
        )
    assert route == "product_rag"
    assert "product" in reason.lower()


def test_route_mixed_tied_goes_general():
    with patch("core.models.router._probe_top_score", return_value=0.5):
        route, reason = route_question(
            "Potato late blight — explain integrated pest management before spraying",
            "late blight ipm integrated pest",
        )
    assert route == "general_rag"
    assert "mixed" in reason.lower() or "guidance" in reason.lower() or "field" in reason.lower()


def test_route_meta_to_base_llm():
    with patch("core.models.router._probe_top_score") as probe:
        route, reason = route_question("who are you", "who are you")
    assert route == "base_llm"
    assert "conversational" in reason.lower()
    probe.assert_not_called()


def test_route_strong_product_intent():
    with patch("core.models.router._probe_top_score") as probe:
        route, reason = route_question(
            "what product should I use to manage potato infection",
            "potato infection product",
        )
    assert route == "product_rag"
    assert "product recommendation" in reason.lower()
    probe.assert_not_called()


def test_route_image_describe_with_vision():
    with patch("core.models.router._probe_top_score") as probe:
        route, reason = route_question(
            "what can u see in this image",
            "what can u see",
            image_analysis="Diagram shows TerraMind system flow.",
        )
    assert route == "base_llm"
    assert "photo" in reason.lower()
    probe.assert_not_called()


def test_route_catalog_fungicide_question():
    with patch("core.models.router._probe_top_score") as probe:
        route, reason = route_question(
            "which of your catalog fungicides would fit the potato problem we discussed",
            "catalog fungicides potato",
        )
    assert route == "product_rag"
    probe.assert_not_called()


def test_route_hello_again_to_base_llm():
    with patch("core.models.router._probe_top_score") as probe:
        route, _ = route_question("hello again", "hello again")
    assert route == "base_llm"
    probe.assert_not_called()


def test_route_gibberish_to_base_llm():
    with patch("core.models.router._probe_top_score") as probe:
        route, reason = route_question("dadada", "dadada")
    assert route == "base_llm"
    assert "unclear" in reason.lower() or "conversational" in reason.lower()
    probe.assert_not_called()


def test_route_vague_plant_to_base_llm():
    with patch("core.models.router._probe_top_score") as probe:
        route, reason = route_question("me wnt to plant how", "me wnt to plant how")
    assert route == "base_llm"
    probe.assert_not_called()


def test_route_hypothetical_product_to_base_llm():
    with patch("core.models.router._probe_top_score") as probe:
        route, _ = route_question(
            "how would u help me if i asked for a product?",
            "how would u help if asked for product",
        )
    assert route == "base_llm"
    probe.assert_not_called()


def test_route_arabic_product_to_product_rag():
    with patch("core.models.router._probe_top_score") as probe:
        route, reason = route_question(
            "اريد ان تعطيني منتج يساعد في تحسين التربة",
            "منتج تحسين التربة",
        )
    assert route == "product_rag"
    assert "product" in reason.lower()
    probe.assert_not_called()


def test_route_arabic_how_can_you_help_to_base_llm():
    with patch("core.models.router._probe_top_score") as probe:
        route, _ = route_question("كيف تستطيع مساعدتي؟", "كيف تستطيع مساعدتي")
    assert route == "base_llm"
    probe.assert_not_called()


def test_route_arabic_what_confusion_to_base_llm():
    with patch("core.models.router._probe_top_score") as probe:
        route, _ = route_question("ماذا؟", "ماذا")
    assert route == "base_llm"
    probe.assert_not_called()
