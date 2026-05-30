"""Ask a question using the base LLM only (no RAG)."""

import argparse

import _bootstrap  # noqa: F401

from dotenv import load_dotenv

from src.base_llm import answer_without_rag

load_dotenv()


def main():
    parser = argparse.ArgumentParser(description="Run TerraMind base LLM (no retrieval).")
    parser.add_argument("question", nargs="?", default="How do I treat tomato early blight?")
    args = parser.parse_args()

    answer = answer_without_rag(args.question)
    print("\n=== Base LLM (no RAG) ===\n")
    print(answer)


if __name__ == "__main__":
    main()
