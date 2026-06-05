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


# Only the User Manual is recursively split because it is
# the largest field in the catalog (~2700 chars on average).
# Other sections are kept intact to preserve their semantic meaning.

MANUAL_SPLITTER =(

    RecursiveCharacterTextSplitter(
    chunk_size=900,
    chunk_overlap=120,
    )
)

# Create a lightweight identity chunk that helps retrieval
# when users ask about a specific product, product type,
# or package size.

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


# Create a compact product overview chunk containing
# the most important operational information:
# product type, ingredients, crops, instructions,
# and package size.
#
# Short fields such as instructions and specification
# are embedded together instead of creating standalone
# chunks to avoid low-information embeddings.

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

# Create a dedicated usage/dosage chunk.
#
# Usage information is separated from the summary because
# users frequently ask operational questions such as:
# "How should I apply this product?"
# "What is the dosage?"
#
# This improves retrieval precision for application-related queries.

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

# Split the User Manual into multiple chunks.
#
# The manual contains the majority of product knowledge
# (diseases, mechanisms, precautions, efficacy, etc.)
# and is too large to store as a single chunk.
#
# Each chunk keeps the product name as context to improve
# retrieval quality after splitting.

def create_manual_chunks(
    product: Document,
) -> list[Document]:
    """
    Split product manual into
    multiple chunks.
    """

    metadata = product.metadata

    sections = metadata["sections"]

    manual_text = (
        sections["manual"]
        .strip()
    )

    chunk_texts = (
        MANUAL_SPLITTER
        .split_text(manual_text)
    )

    manual_chunks = []

    for index, chunk_text in enumerate(
        chunk_texts,
        start=1,
    ):

        chunk_content = f"""
Product Name: {metadata["product_name"]}

Manual:

{chunk_text}
""".strip()

        manual_chunks.append(
            Document(
                page_content=chunk_content,
                metadata={
                    "product_id":
                        metadata["product_id"],

                    "product_name":
                        metadata["product_name"],

                    "chunk_type":
                        "manual",

                    "chunk_index":
                        index,
                },
            )
        )

    return manual_chunks

# Build all retrieval chunks for a single product.
#
# Final chunk architecture:
# - Identity Chunk
# - Operational Summary Chunk
# - Usage Chunk (if available)
# - Manual Chunks

def build_product_chunks(
    product: Document,
) -> list[Document]:
    """
    Create all chunks for a product.
    """

    chunks = []

    chunks.append(
        create_identity_chunk(product)
    )

    chunks.append(
        create_operational_summary_chunk(
            product
        )
    )

    usage_chunk = (
        create_usage_chunk(product)
    )

    if usage_chunk is not None:

        chunks.append(
            usage_chunk
        )

    chunks.extend(
        create_manual_chunks(product)
    )

    return chunks

# Process the entire catalog and generate all retrieval-ready
# chunks that will later be embedded and stored in the vector database.

def build_all_chunks(
    products: list[Document],
) -> list[Document]:
    """
    Create chunks for the entire catalog.
    """

    all_chunks = []

    for product in products:

        all_chunks.extend(
            build_product_chunks(
                product
            )
        )

    return all_chunks


#################################
#Test


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

def test_manual_chunks(
    products: list[Document],
) -> None:

    manual_chunks = (
        create_manual_chunks(
            products[0]
        )
    )

    print(
        f"\nCreated "
        f"{len(manual_chunks)} "
        f"manual chunks\n"
    )

    print(
        manual_chunks[0]
        .page_content[:1000]
    )

    print("\nMETADATA\n")

    print(
        manual_chunks[0]
        .metadata
    )


# Quick pipeline validation:
# 1. Load products
# 2. Generate all chunks
# 3. Print basic statistics
#
# This block is only used for local testing and debugging.

if __name__ == "__main__":

    products = load_products(
        Path(
            "data/raw/text/ProductCatalog(En).xlsx"
        )
    )

    all_chunks = build_all_chunks(
        products
    )

    print(
        f"Products: {len(products)}"
    )

    print(
        f"Chunks: {len(all_chunks)}"
    )

    print("\nFirst Chunk:\n")

    print(
        all_chunks[0].page_content
    )

    print("\nMetadata:\n")

    print(
        all_chunks[0].metadata
    )

    # test_manual_chunks(products)
    # test_usage_chunk(products)
    # test_summary_chunk(products)
    # test_identity_chunk(products)