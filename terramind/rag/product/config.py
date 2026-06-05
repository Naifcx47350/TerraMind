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