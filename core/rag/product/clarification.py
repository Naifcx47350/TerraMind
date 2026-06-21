"""Clarification detection scaffolding for Product RAG.

This module is intentionally not wired into the live Product RAG flow yet. It gives
the clarification owner a small, typed place to implement "ask a follow-up first"
logic without changing retrieval/generation contracts.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class ClarificationReason(str, Enum):
    """High-level reason a product question may need a follow-up."""

    MISSING_PRODUCT = "missing_product"
    MISSING_CROP_OR_PROBLEM = "missing_crop_or_problem"
    AMBIGUOUS_REFERENCE = "ambiguous_reference"
    AMBIGUOUS_QUANTITY = "ambiguous_quantity"


@dataclass(frozen=True)
class ClarificationDecision:
    """Result returned by the future clarification classifier."""

    needs_clarification: bool
    reason: ClarificationReason | None = None
    question: str | None = None


def classify_clarification_need(
    user_question: str,
    *,
    chat_history: list[dict] | None = None,
    retrieved_product_names: list[str] | None = None,
) -> ClarificationDecision:
    """Return whether Product RAG should ask a follow-up before retrieval/answering.

    TODO(owner: clarification):
    - Detect vague follow-ups like "how much water should I mix it with?" when no
      product is recoverable from chat history.
    - Distinguish vague product requests from valid broad catalog questions.
    - Use retrieved product names to ask targeted follow-ups when several products match.
    - Keep this function side-effect free so it can be called from product_rag,
      streaming, advisory, or tests.
    """
    _ = (user_question, chat_history, retrieved_product_names)
    return ClarificationDecision(needs_clarification=False)
