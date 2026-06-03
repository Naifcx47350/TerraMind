"""General RAG — command-line entry: python -m terramind.rag.general.cli"""

import argparse

from terramind.rag.general.pipeline import (
    answer_with_rag,
    init_general_rag,
)
from terramind.rag.general.retrieve import retrieve_chunks

DEFAULT_QUESTION = (
    "A potato farmer has repeated late blight outbreaks and wants to reduce pesticide use. "
    "Based on the provided document, what integrated disease management steps should they take "
    "before relying on fungicides, and when should fungicide application be planned?"
)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="TerraMind general agriculture RAG"
    )
    parser.add_argument(
        "--reset",
        action="store_true",
        help="Delete and rebuild the Chroma index",
    )
    parser.add_argument(
        "question",
        nargs="?",
        default=None,
        help="Optional test question",
    )
    args = parser.parse_args()

    query = args.question or DEFAULT_QUESTION
    db = init_general_rag(reset=args.reset)
    print(f"General RAG ready ({db._collection.count()} vectors in index)")

    print("\n--- Retrieved chunks ---")
    retrieved = retrieve_chunks(db, query)
    for i, hit in enumerate(retrieved, start=1):
        section = hit.metadata.get("h2") or hit.metadata.get("h1") or "n/a"
        print(f"\nResult {i} | {hit.metadata.get('title', 'n/a')} | {section}")
        print(hit.page_content[:300], "...")

    print("\n--- RAG answer ---")
    result = answer_with_rag(db, query, generation_prompt=query)
    from terramind.rag.general.pipeline import sources_from_retrieved

    labels = [s["title"] for s in sources_from_retrieved(retrieved)]
    print(f"\n{result['answer']}\n\n---\n\nSources: {labels}")


if __name__ == "__main__":
    main()
