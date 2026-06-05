"""
Product RAG — optional text splitting.

TODO: Usually NOT needed — each Excel row is already one product document.
  - Only implement if you split long User Manual text into smaller chunks
  - Otherwise leave empty and import nothing from pipeline
See docs/PROJECT_STATUS.md (product migration).
"""
from pathlib import Path

from langchain_core.documents import Document
from langchain_text_splitters import (
    RecursiveCharacterTextSplitter,
)

from load import load_products


MANUAL_SPLITTER = RecursiveCharacterTextSplitter(
    chunk_size=1000,
    chunk_overlap=200,
)

def create_identity_chunk(
    product: Document,
) -> Document:
    """
    Create a product identity chunk.
    """

    metadata = product.metadata

    sections = metadata["sections"]

    identity_text = f"""
Product ID: {metadata["product_id"]}

Product Name: {metadata["product_name"]}

Product Type:
{sections["product_type"]}

Pack Size:
{sections["specification"]}
""".strip()

    return Document(
        page_content=identity_text,
        metadata={
            "product_id": metadata["product_id"],
            "product_name": metadata["product_name"],
            "chunk_type": "identity",
        },
    )

def test_identity_chunk(
    products: list[Document],
) -> None:

    identity_chunk = create_identity_chunk(
        products[0]
    )

    print("\nIDENTITY CHUNK\n")

    print(identity_chunk.page_content)

    print("\nMETADATA\n")

    print(identity_chunk.metadata)

def create_operational_summary_chunk(
    product: Document,
) -> Document:
    """
    Create an operational summary chunk.
    """

    metadata = product.metadata

    sections = metadata["sections"]

    summary_text = f"""
Product Name: {metadata["product_name"]}

Product Type:
{sections["product_type"]}

Main Ingredients:
{sections["ingredients"]}

Target Crops:
{sections["crops"]}

Instructions:
{sections["instructions"]}

Pack Size:
{sections["specification"]}
""".strip()

    return Document(
        page_content=summary_text,
        metadata={
            "product_id": metadata["product_id"],
            "product_name": metadata["product_name"],
            "chunk_type": "summary",
        },
    )

def create_usage_chunk(
    product: Document,
) -> Document | None:
    """
    Create a usage and dosage chunk.
    """

    metadata = product.metadata

    sections = metadata["sections"]

    usage_text = sections["usage"].strip()

    if (
        not usage_text
        or usage_text == "___"
    ):
        return None

    chunk_text = f"""
Product Name: {metadata["product_name"]}

Usage and Dosage:

{usage_text}
""".strip()

    return Document(
        page_content=chunk_text,
        metadata={
            "product_id": metadata["product_id"],
            "product_name": metadata["product_name"],
            "chunk_type": "usage",
        },
    )


def test_summary_chunk(
    products: list[Document],
) -> None:

    summary_chunk = (
        create_operational_summary_chunk(
            products[0]
        )
    )

    print("\nSUMMARY CHUNK\n")

    print(summary_chunk.page_content)

    print("\nMETADATA\n")

    print(summary_chunk.metadata)

def test_usage_chunk(
    products: list[Document],
) -> None:

    usage_chunk = create_usage_chunk(
        products[0]
    )

    print("\nUSAGE CHUNK\n")

    print(usage_chunk.page_content)

    print("\nMETADATA\n")

    print(usage_chunk.metadata)


if __name__ == "__main__":

    products = load_products(
        Path(
            "data/raw/text/ProductCatalog(En).xlsx"
        )
    )
    
    print(
    len(
        products[0]
        .metadata["sections"]["manual"]
    )
)

    test_usage_chunk(products)
    #test_summary_chunk(products)
    #test_identity_chunk(products) 