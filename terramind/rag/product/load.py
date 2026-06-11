"""Product RAG — load translated Excel catalog into LangChain Documents."""
# Product Loading
#
# Load the product catalog from Excel and convert each product into a
# structured LangChain Document.
#
# Output:
# One Document per product containing:
# - Product metadata (ID, name)
# - Organized product sections (ingredients, crops, usage, manual, etc.)
#
# These Product Documents are later used by chunk.py to generate
# retrieval-ready chunks for the Product RAG pipeline.


from pathlib import Path

import pandas as pd
from langchain_core.documents import Document

from terramind.rag.product.config import CATEGORY_PATH


def _clean(value) -> str:
    """Turn a cell into a trimmed string; NaN/None -> empty string."""
    if pd.isna(value):
        return ""
    return str(value).strip()

def load_catalog(
    catalog_path: Path,
    category_path: Path | None = CATEGORY_PATH,
) -> pd.DataFrame:
    """Load the translated product catalog and attach category columns if present."""
    catalog = pd.read_excel(catalog_path)

    if category_path and category_path.exists():
        categories = pd.read_excel(category_path)
        if "English name" in catalog.columns and "Product Name" in categories.columns:
            catalog = catalog.merge(
                categories,
                how="left",
                left_on="English name",
                right_on="Product Name",
            )

    return catalog


# Map internal section names to Excel column names.
# These sections become the structured product content used
# throughout the Product RAG pipeline.


FIELD_MAPPING = {
    "product_type": "Product Type",
    "crops": "Corresponding crops/plants",
    "ingredients": "Main ingredients",
    "usage": "Usage and dosage",
    "instructions": "Instructions for use (dilute with water)",
    "specification": "Specification",
    "manual": "User Manual",
}


# Product Document Builder
#
# Transform each catalog row into a structured Product Document.
#
# Each document stores:
# - Product identity metadata
# - Product content grouped into logical sections
#
# Chunk generation is intentionally deferred to chunk.py.
def build_products(
    catalog_df: pd.DataFrame,
) -> list[Document]:
    """
    Convert each catalog row into
    one Product Document.
    """

    products = []
    
    # Process products one row at a time
    for _, row in catalog_df.iterrows():

        product_name = _clean(
            row["English name"]
        )
        
        # Collect all product sections into a structured dictionary
        sections = {}
        
        # Extract catalog content and organize it by section
        for (
            section_name,
            column_name,
        ) in FIELD_MAPPING.items():

            value = _clean(
                row[column_name]
            )

            sections[section_name] = value
        
        # Store product information as a LangChain Document
        # Metadata carries the structured content used by chunk.py
        products.append(
            Document(
                page_content="",
                metadata={
                    "product_id": str(
                        _clean(row["Product ID"])
                    ),

                    "product_name": product_name,

                    "primary_category": _clean(
                        row.get("Primary Category")
                    ),

                    "secondary_category": _clean(
                        row.get("Secondary Category")
                    ),

                    "source": catalog_path.name,

                    "sections": sections,
                },
            )
        )

    return products

# Product Loader
# 
# Main entry point for the loading stage.
#
# Pipeline:
# Excel Catalog
# → DataFrame
# → Product Documents
#
# Returns a list of Product Documents ready for chunk generation.

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
            "data/raw/product_catalog/translated/product_catalog_en.xlsx"
        )
    )

    print(
        f"Loaded {len(products)} products"
    )

    print("\nFirst Product:\n")

    print(
        products[0].metadata
    )

    