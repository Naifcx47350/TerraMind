"""Advisory mode — meta / identity questions should not run full RAG."""

from terramind.meta_questions import advisory_meta_answer, is_meta_question


def test_is_meta_question_identity():
    assert is_meta_question("who are you")
    assert is_meta_question("Who are you?")
    assert is_meta_question("hello")
    assert is_meta_question("what can you do")


def test_is_meta_question_not_field_task():
    assert not is_meta_question(
        "My tomatoes have brown spots — which catalog product should I use?"
    )
    assert not is_meta_question("who are you " + "x" * 200)


def test_image_describe_question():
    from terramind.meta_questions import is_image_describe_question

    assert is_image_describe_question("what can u see in this image")
    assert not is_image_describe_question("how do I treat tomato blight")


def test_strong_product_intent():
    from terramind.meta_questions import has_strong_product_intent

    assert has_strong_product_intent("what product is best for soil")
    assert not has_strong_product_intent("how does crop rotation help soil")


def test_advisory_meta_answer_content():
    text = advisory_meta_answer()
    assert "TerraMind" in text
    assert "Advisory" in text
    assert "product catalog" in text.lower()
    assert "Haloxyfop" not in text
