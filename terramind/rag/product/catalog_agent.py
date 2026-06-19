"""SQL-like product catalog agent.

Answers structured catalog questions directly from the translated Excel dataset,
such as counting products by product type, filtering by ingredient, and listing
products by crop before or alongside vector retrieval.
"""

from __future__ import annotations

import json

from langchain_openai import ChatOpenAI
from dataclasses import dataclass, field
from typing import Any, Literal

import pandas as pd

from terramind.rag.product.config import CATALOG_PATH,CHAT_MODEL

CatalogToolKind = Literal[
    "count_by_category",
    "filter_by_crop",
    "filter_by_ingredient",
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


def load_catalog_tables() -> tuple[pd.DataFrame, None]:
    """Load translated catalog table."""
    catalog = pd.read_excel(CATALOG_PATH)
    return catalog, None


def _normalize_text(value: Any) -> str:
    """Normalize text for simple case-insensitive matching."""
    if pd.isna(value):
        return ""

    return str(value).lower().strip()


def _row_to_result(row: pd.Series) -> dict[str, Any]:
    """Return a small, safe product result row."""
    return {
        "product_id": row.get("Product ID"),
        "product_name": row.get("English name"),
        "product_type": row.get("Product Type"),
        "ingredients": row.get("Main ingredients"),
        "crops": row.get("Corresponding crops/plants"),
    }

def run_catalog_tool(request: CatalogToolRequest) -> CatalogToolResult:
    """Run safe SQL-like catalog operations over the product Excel table."""

    catalog, _ = load_catalog_tables()

    if request.kind == "count_by_category":

        category = _normalize_text(
            request.filters.get("category")
        )

        if not category:
            return CatalogToolResult(
                request=request,
                rows=[],
                summary="Missing category filter.",
            )

        mask = catalog["Product Type"].apply(
            lambda value: category in _normalize_text(value)
        )

        count = int(mask.sum())

        return CatalogToolResult(
            request=request,
            rows=[],
            summary=f"Found {count} products in category '{category}'.",
        )

    if request.kind == "filter_by_crop":

        crop = _normalize_text(
            request.filters.get("crop")
        )
        
        category = _normalize_text(
            request.filters.get("category")
        )

        if not crop:
            return CatalogToolResult(
                request=request,
                rows=[],
                summary="Missing crop filter.",
            )

        mask = catalog["Corresponding crops/plants"].apply(
            lambda value: crop in _normalize_text(value)
        )
        
        if category:
            mask = mask & catalog["Product Type"].apply(
                lambda value: category in _normalize_text(value)
            )

        total = int(mask.sum())

        rows = [
            _row_to_result(row)
            for _, row in catalog[mask].head(20).iterrows()
        ]

        return CatalogToolResult(
            request=request,
            rows=rows,
            summary=(
                f"Found {total} products related to crop '{crop}'"
                + (f" in category '{category}'" if category else "")
                + f". Showing first {len(rows)}."
            ),
        )

    if request.kind == "filter_by_ingredient":

        ingredient = _normalize_text(
            request.filters.get("ingredient")
        )

        if not ingredient:
            return CatalogToolResult(
                request=request,
                rows=[],
                summary="Missing ingredient filter.",
            )

        mask = catalog["Main ingredients"].apply(
            lambda value: ingredient in _normalize_text(value)
        )

        total = int(mask.sum())

        rows = [
            _row_to_result(row)
            for _, row in catalog[mask].head(20).iterrows()
        ]

        return CatalogToolResult(
            request=request,
            rows=rows,
            summary=(
                f"Found {total} products containing ingredient '{ingredient}'. "
                f"Showing first {len(rows)}."
            ),
        )

    return CatalogToolResult(
        request=request,
        rows=[],
        summary=f"Catalog tool kind '{request.kind}' is not supported yet.",
    )
    



def build_catalog_request(user_question: str) -> CatalogToolRequest:
    """Use an LLM to convert a natural language question into a catalog tool request."""

    llm = ChatOpenAI(
        model=CHAT_MODEL,
        temperature=0,
    )

    prompt = f"""
You are a catalog routing agent for an agricultural product catalog.

Convert the user question into exactly one JSON object.

Supported tool kinds:
- count_by_category
- filter_by_crop
- filter_by_ingredient
- unsupported

Use only these filters:
- category
- crop
- ingredient


Rules:
- Use count_by_category for questions asking how many products belong to a product type such as pesticide or assisted growth.
- Use filter_by_ingredient for questions asking which products contain an ingredient.
- Use filter_by_crop for questions asking products related to a crop.
- If the question has both crop and category, include both filters.
- Use unsupported for application instructions, disease control, precautions, summaries, or manual explanation questions.
- Return JSON only. No markdown.

Examples:
Question: Which products contain Bacillus subtilis?
JSON: {{"kind": "filter_by_ingredient", "filters": {{"ingredient": "Bacillus subtilis"}}}}

Question: How many pesticide products are there?
JSON: {{"kind": "count_by_category", "filters": {{"category": "pesticide"}}}}

Question: List assisted growth products for chili pepper.
JSON: {{"kind": "filter_by_crop", "filters": {{"crop": "chili pepper", "category": "assisted growth"}}}}

Question: How should I apply Bacteria Clear?
JSON: {{"kind": "unsupported", "filters": {{}}}}

User question:
{user_question}
"""

    response = llm.invoke(prompt)

    try:
        data = json.loads(response.content or "{}")

        kind = data.get("kind", "unsupported")
        filters = data.get("filters", {})

        if kind not in {
            "count_by_category",
            "filter_by_crop",
            "filter_by_ingredient",
            "unsupported",
        }:
            kind = "unsupported"
            filters = {}

        return CatalogToolRequest(
            kind=kind,
            filters=filters,
        )

    except Exception:
        return CatalogToolRequest(
            kind="unsupported",
            filters={},
        )
        
def route_product_question(
    request: CatalogToolRequest,
) -> Literal["catalog_agent", "product_rag"]:
    """Decide whether a parsed catalog request should use the catalog agent or Product RAG."""

    if request.kind == "unsupported":
        return "product_rag"

    return "catalog_agent"


def answer_catalog_question_from_request(
    request: CatalogToolRequest,
) -> str:
    """Run the catalog agent from an already parsed tool request."""

    if request.kind == "unsupported":
        return "This question should be answered by Product RAG."

    result = run_catalog_tool(
        request
    )

    return format_catalog_answer(
        result
    )


def answer_catalog_question(user_question: str) -> str:
    """Catalog Agent: parse question once, run tool, and format the answer."""

    request = build_catalog_request(
        user_question
    )

    return answer_catalog_question_from_request(
        request
    )
    
    
def format_catalog_answer(result: CatalogToolResult) -> str:
    """Format catalog tool result into a user-facing answer."""

    if not result.rows:
        return result.summary

    lines = [result.summary]

    for row in result.rows:
        lines.append(
            f"- {row['product_name']} ({row['product_id']}) — {row['product_type']}"
        )

    return "\n".join(lines)

if __name__ == "__main__":

    questions = [
        "Which products contain Bacillus subtilis?",
        "Which products contain imidacloprid?",
        "List products registered for citrus.",
        "How many pesticide products are there?",
        "List assisted growth products for chili pepper.",
        "How should I apply Bacteria Clear?",
        "What diseases does Citrus Bacteria Clear control?",
        "Summarize the product manual for Bacteria Clear.",
    ]

    for question in questions:

        request = build_catalog_request(
            question
        )

        route = route_product_question(
            request
        )

        print("\n---")
        print("Question:", question)
        print("Request:", request)
        print("Route:", route)

        if route == "catalog_agent":
            print(
                answer_catalog_question_from_request(
                    request
                )
            )