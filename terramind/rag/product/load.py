"""
Product RAG — load Excel catalog into LangChain Documents.

TODO: Move from Rag_Pc.py:
  - Read ProductCatalog(En).xlsx (and category sheet if used)
  - Build one Document per product row with metadata: product_id, product_name, source file
  - Export: load_catalog() -> list[Document]
See docs/PROJECT_STATUS.md (product migration).
"""

from pathlib import Path

import pandas as pd
from langchain_core.documents import Document

def load_catalog(
    catalog_path: Path,
) -> pd.DataFrame:
    """
    Load the product catalog Excel file.
    """

    return pd.read_excel(catalog_path)

FIELD_MAPPING = {
    "product_type": "Product Type",
    "crops": "Corresponding crops/plants",
    "ingredients": "Main ingredients",
    "usage": "Usage and dosage",
    "instructions": "Instructions for use (dilute with water)",
    "specification": "Specification",
    "manual": "User Manual",
}

def build_products(
    catalog_df: pd.DataFrame,
) -> list[Document]:
    """
    Convert each catalog row into
    one Product Document.
    """

    products = []

    for _, row in catalog_df.iterrows():

        product_name = str(
            row["English name"]
        ).strip()

        sections = {}

        for (
            section_name,
            column_name,
        ) in FIELD_MAPPING.items():

            value = str(
                row[column_name]
            ).strip()

            sections[section_name] = value

        products.append(
            Document(
                page_content="",
                metadata={
                    "product_id": str(
                        row["Product ID"]
                    ).strip(),

                    "product_name": product_name,

                    "sections": sections,
                },
            )
        )

    return products


def load_products(
    catalog_path: Path,
) -> list[Document]:
    """
    Load product catalog and build
    Product Documents.
    """

    catalog_df = load_catalog(
        catalog_path
    )

    products = build_products(
        catalog_df
    )

    return products

# Run this file directly to verify product loading
if __name__ == "__main__":

    products = load_products(
        Path(
            "data/raw/text/ProductCatalog(En).xlsx"
        )
    )

    print(
        f"Loaded {len(products)} products"
    )

    print("\nFirst Product:\n")

    print(
        products[0].metadata
    )