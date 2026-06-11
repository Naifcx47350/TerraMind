"""SQL-like product catalog agent scaffolding.

Future goal: answer structured catalog questions directly from the translated Excel
dataset before or alongside vector retrieval, for example:

- "How many products belong to this category?"
- "Which products contain ingredient X?"
- "List products registered for crop Y."

This file is not wired into runtime yet; it defines a small interface for the teammate
building catalog tools.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal

import pandas as pd

from terramind.rag.product.config import CATALOG_PATH, CATEGORY_PATH

CatalogToolKind = Literal[
    "count_by_category",
    "filter_by_crop",
    "filter_by_ingredient",
    "lookup_product",
    "unsupported",
]


@dataclass(frozen=True)
class CatalogToolRequest:
    """A structured request that can later be produced by an LLM/tool router."""

    kind: CatalogToolKind
    filters: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class CatalogToolResult:
    """Structured result from a catalog table operation."""

    request: CatalogToolRequest
    rows: list[dict[str, Any]]
    summary: str


def load_catalog_tables() -> tuple[pd.DataFrame, pd.DataFrame | None]:
    """Load translated catalog and optional translated category table."""
    catalog = pd.read_excel(CATALOG_PATH)
    categories = pd.read_excel(CATEGORY_PATH) if CATEGORY_PATH.exists() else None
    return catalog, categories


def run_catalog_tool(request: CatalogToolRequest) -> CatalogToolResult:
    """Run a future SQL-like catalog operation.

    TODO(owner: catalog agent):
    - Implement safe filtering/counting over `load_catalog_tables()`.
    - Normalize column names and user terms before matching.
    - Return small row sets only; never dump the entire catalog into the prompt.
    - Decide how this should combine with Product RAG retrieval:
      direct answer, retrieval hint, or extra context block.
    """
    return CatalogToolResult(
        request=request,
        rows=[],
        summary="Catalog tool is not implemented yet.",
    )
