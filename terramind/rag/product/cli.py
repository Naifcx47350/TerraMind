"""Product RAG command-line entry."""

from __future__ import annotations

import argparse

from terramind.rag.product.pipeline import (
    answer_with_rag,
    get_product_db,
    init_product_rag,
    retrieve_products,
    sources_from_retrieved,
)

DEFAULT_QUESTION = (
    "What categories of usage does 10% Glufosinate-Ammonium belong to, "
    "and how can I use it?"
)


def main() -> None:
    parser = argparse.ArgumentParser(description="TerraMind product catalog RAG")
    parser.add_argument(
        "--reset",
        action="store_true",
        help="Delete and rebuild the product Chroma index.",
    )
    parser.add_argument(
        "question",
        nargs="?",
        default=DEFAULT_QUESTION,
        help="Question about a catalog product.",
    )
    args = parser.parse_args()

    db = init_product_rag(reset=args.reset) if args.reset else get_product_db()
    print(f"Product RAG ready ({db._collection.count()} vectors in index)")

    print("\n--- Retrieved product chunks ---")
    for i, hit in enumerate(retrieve_products(db, args.question), start=1):
        print(
            f"\nChunk {i} | {hit.metadata.get('product_name', 'n/a')} "
            f"({hit.metadata.get('product_id', 'n/a')})"
        )
        print(hit.page_content[:250], "...")

    result = answer_with_rag(db, args.question)
    print("\n--- Answer ---")
    print(result.get("answer", ""))

    print("\n--- Sources ---")
    for source in sources_from_retrieved(result.get("retrieved", [])):
        print(f"- {source.get('title')} [{source.get('source')}]")


if __name__ == "__main__":
    main()
