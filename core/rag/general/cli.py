"""General RAG — CLI: build index, inspect corpus, eval retrieval, test Q&A."""

import argparse
import sys

from core.rag.general.eval import inspect_corpus, run_retrieval_eval
from core.rag.general.pipeline import (
    answer_with_rag,
    init_general_rag,
    sources_from_retrieved,
)
from core.rag.general.retrieve import retrieve_chunks
from core.rag.scoring import aggregate_retrieval_score, chunk_relevance, confidence_from_retrieval

DEFAULT_QUESTION = (
    "A potato farmer has repeated late blight outbreaks and wants to reduce pesticide use. "
    "What integrated disease management steps should they take before relying on fungicides?"
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
        "--inspect",
        action="store_true",
        help="Load each source file and print char counts + preview (no index)",
    )
    parser.add_argument(
        "--dry-load",
        action="store_true",
        help="Alias for --inspect",
    )
    parser.add_argument(
        "--eval-retrieval",
        action="store_true",
        help="Run golden retrieval questions (no LLM); requires index",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Print per-chunk relevance scores (with default question / retrieval preview)",
    )
    parser.add_argument(
        "question",
        nargs="?",
        default=None,
        help="Optional test question (full RAG answer)",
    )
    args = parser.parse_args()

    if args.inspect or args.dry_load:
        warnings = inspect_corpus(dry_load=True)
        sys.exit(1 if warnings else 0)

    db = init_general_rag(reset=args.reset)
    print(f"General RAG ready ({db._collection.count()} vectors in index)")
    if args.reset and args.question is None:
        return

    if args.eval_retrieval:
        summary = run_retrieval_eval(db)
        sys.exit(0 if summary.get("rate_pct", 0) >= 80 else 1)

    query = args.question or DEFAULT_QUESTION

    print("\n--- Retrieved chunks ---")
    retrieved = retrieve_chunks(db, query)
    for i, hit in enumerate(retrieved, start=1):
        section = hit.metadata.get("h2") or hit.metadata.get("h1") or "n/a"
        score = chunk_relevance(hit)
        score_txt = f" | relevance={score:.3f}" if score is not None else ""
        print(
            f"\nResult {i} | {hit.metadata.get('filename', 'n/a')} "
            f"| {hit.metadata.get('corpus_topic', '')} | {section}{score_txt}"
        )
        print(hit.page_content[:300], "...")

    if args.verbose:
        agg = aggregate_retrieval_score(retrieved)
        conf = confidence_from_retrieval(retrieved)
        print(
            f"\nRetrieval: best_score={agg:.3f} confidence={conf} chunks={len(retrieved)}"
            if agg is not None
            else f"\nRetrieval: confidence={conf} chunks={len(retrieved)}"
        )

    print("\n--- RAG answer ---")
    result = answer_with_rag(db, query, generation_prompt=query)
    sources = sources_from_retrieved(result["retrieved"])
    labels = [s["title"] for s in sources]
    print(f"\n{result['answer']}\n\n---\n\nSources: {labels}")
    if args.verbose:
        from core.rag.scoring import rag_metrics

        m = rag_metrics(result["retrieved"], sources)
        rs = m.get("retrieval_score")
        print(
            f"Answer metrics: confidence={m['confidence']} "
            f"retrieval_score={rs:.3f} chunks={m['retrieved_chunks']}"
            if rs is not None
            else f"Answer metrics: confidence={m['confidence']} chunks={m['retrieved_chunks']}"
        )


if __name__ == "__main__":
    main()
