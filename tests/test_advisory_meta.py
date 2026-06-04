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
    assert has_strong_product_intent(
        "which of your catalog fungicides would fit the potato problem"
    )
    assert not has_strong_product_intent("how does crop rotation help soil")


def test_meta_greeting_and_summary():
    assert is_meta_question("hello again")
    assert is_meta_question("summarize our conversation in three bullet points")


def test_clarification_and_gibberish():
    from terramind.meta_questions import is_clarification_question, has_strong_product_intent

    assert is_clarification_question("dadada")
    assert is_clarification_question("noncess")
    assert is_meta_question("?are you ok")
    assert is_clarification_question("me wnt to plant how")
    assert not is_clarification_question(
        "What are integrated pest management steps before spraying?"
    )
    ar_product = "اريد ان تعطيني منتج يساعد في تحسين التربة"
    assert has_strong_product_intent(ar_product)
    assert not is_clarification_question(ar_product)


def test_hypothetical_questions_are_meta():
    assert is_meta_question("how would u help me if i asked for a product?")
    assert is_meta_question("what if i asked about general agricultural info")


def test_arabic_meta_and_clarification():
    from terramind.meta_questions import is_clarification_question

    assert is_meta_question("كيف تستطيع مساعدتي؟")
    assert is_meta_question("ماذا؟")
    assert is_meta_question("لماذا تطبع جوابي")
    assert not is_clarification_question("كيف تستطيع مساعدتي؟")


def test_advisory_meta_answer_content():
    text = advisory_meta_answer()
    assert "TerraMind" in text
    assert "Advisory" in text
    assert "product catalog" in text.lower()
    assert "Haloxyfop" not in text
