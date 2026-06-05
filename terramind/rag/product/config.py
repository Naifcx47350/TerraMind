"""
Product RAG — configuration constants.

TODO: Move from Rag_Pc.py (top ~50 lines):
  - REPO_ROOT / PROJECT_ROOT pointing at TerraMind repo root
  - CATALOG_PATH, CATEGORY_PATH, CHROMA_PATH (keep vectorstore/chroma_products)
  - EMBEDDING_MODEL, CHAT_MODEL, RETRIEVAL_K
  - Excel column names + PRODUCT_FIELDS dict
Then update Rag_Pc.py to `from terramind.rag.product.config import ...` until Rag_Pc is removed.
See docs/PROJECT_STATUS.md (product migration).
"""

from langchain_core.prompts import ChatPromptTemplate
from pathlib import Path


# ---------------------------------------------------------------------
# Project Paths
# ---------------------------------------------------------------------

PROJECT_ROOT = (
    Path(__file__)
    .resolve()
    .parents[3]
)

CATALOG_PATH = (
    PROJECT_ROOT
    / "data/raw/text/ProductCatalog(En).xlsx"
)

CATEGORY_PATH = (
    PROJECT_ROOT
    / "data/raw/text/Product_catagorys(En).xlsx"
)

CHROMA_PATH = (
    PROJECT_ROOT
    / "vectorstore/chroma_products"
)


# ---------------------------------------------------------------------
# Models
# ---------------------------------------------------------------------

EMBEDDING_MODEL = (
    "text-embedding-3-small"
)

CHAT_MODEL = (
    "gpt-4o-mini"
)


# ---------------------------------------------------------------------
# Retrieval
# ---------------------------------------------------------------------

RETRIEVAL_K = 4


# ---------------------------------------------------------------------
# Excel Columns
# ---------------------------------------------------------------------

COL_PRODUCT_ID = "Product ID"

COL_LEGACY_NAME = (
    "Product Name"
)

COL_PRODUCT_NAME = (
    "English name"
)




CHAT_MODEL = "gpt-4o-mini"



RAG_PROMPT = ChatPromptTemplate.from_template(
    """You are TerraMind product catalog assistant — helping growers choose and use
products safely from the company catalog.

Retrieved product records:
{context}

User message (may include brief notes from an uploaded crop photo):
{question}

How to respond:
- Answer what they actually asked first (e.g. what is wrong with the crop, is it serious,
  which catalog product fits, how to mix/apply, timing, safety) — not a generic template.
- If they sent a photo: weave a short observation into your answer (symptoms, severity);
  do not output a separate "image analysis" report or repeat a numbered vision checklist.
- When a product recommendation is needed: name the best match from the catalog and explain
  why it fits the crop/problem; give use, dilution, dosage, and crops only where the
  catalog text provides them.
- Do not force every reply to list Product ID, User Manual, and all catalog fields.
  Include IDs or manual quotes only when they help the user.
- If several products match, lead with the strongest fit; mention one alternative only if useful.
- If a detail is missing in the catalog, say so once and point to the product label — never
  invent rates, ingredients, or SKUs.
-Answer the user's question directly first.
 Do not include unrelated product information unless it helps answer the question.

Formatting:
- Use clear Markdown the chat can render: short paragraphs, **bold** for emphasis,
  ### headings for sections, and bullet or numbered lists for steps.

Rules:
- Product facts, rates, and SKUs must come ONLY from the retrieved records above.
- Be practical and concise unless they ask for full label-level detail.
"""

)