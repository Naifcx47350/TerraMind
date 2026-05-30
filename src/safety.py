"""Basic safety helpers (expanded in Phase 4)."""

DOSAGE_KEYWORDS = ("dosage", "dose", "rate", "how much", "ml", "liter", "hectare", "per ha")
MIX_KEYWORDS = ("mix", "tank-mix", "tank mix", "combine with", "together with")


def question_mentions_dosage(question: str) -> bool:
    q = question.lower()
    return any(k in q for k in DOSAGE_KEYWORDS)


def question_mentions_mixing(question: str) -> bool:
    q = question.lower()
    return any(k in q for k in MIX_KEYWORDS)


def context_has_dosage_info(context: str) -> bool:
    """Rough check whether retrieved context contains numeric dosage cues."""
    lowered = context.lower()
    if not any(k in lowered for k in ("l per", "ml", "g/l", "hectare", "per ha", "application")):
        return False
    return any(char.isdigit() for char in context)
