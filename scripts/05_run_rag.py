"""Ask a question using TerraMind RAG."""

import argparse

import _bootstrap  # noqa: F401

from dotenv import load_dotenv

from src.base_llm import answer_without_rag
from src.rag_pipeline import answer_with_rag

load_dotenv()


def _print_sources(sources: list[dict]) -> None:
    if not sources:
        print("  (none)")
        return
    for s in sources:
        print(f"  - {s.get('title')} | {s.get('source')} | {s.get('category')}")


def main():
    parser = argparse.ArgumentParser(description="Run TerraMind RAG pipeline.")
    parser.add_argument("question", nargs="?", default="How do I treat tomato early blight?")
    parser.add_argument(
        "--compare",
        action="store_true",
        help="Also print base LLM answer for side-by-side comparison.",
    )
    args = parser.parse_args()

    result = answer_with_rag(args.question)

    print("\n=== TerraMind RAG ===\n")
    print(result["answer"])
    print("\n--- Retrieved sources ---")
    _print_sources(result["sources"])

    if args.compare:
        base = answer_without_rag(args.question)
        print("\n=== Base LLM (no RAG) ===\n")
        print(base)


if __name__ == "__main__":
    main()
