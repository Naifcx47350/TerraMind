"""Advisory combined answer section splitting."""

from terramind.models.advisory import split_advisory_sections


def test_split_advisory_sections():
    merged = (
        "### Public agriculture guidance\n\n"
        "Use crop rotation for soil health.\n\n"
        "### Company product catalog\n\n"
        "No catalog product applies to this greeting."
    )
    general, product = split_advisory_sections(merged)
    assert "crop rotation" in general
    assert "No catalog product" in product
    assert "###" not in general
    assert "###" not in product
