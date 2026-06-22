"""
Run a multiple-choice (MCQ) evaluation over the Product RAG, using
mcq_product.csv.

Same logic as run_mcq_general.py, but:
    - retrieval + generation both go through generate_answer(db, question)
      (Product RAG has no separate retrieval_query/generation_prompt split)
    - the MCQ instruction is appended to the question text so retrieval
      still sees the product name/ID and the LLM still gets the
      single-letter instruction

Saves a detailed report to reports/mcq_product_report.json.

Run:
    python -m terramind.FullEvaluation.heuristic_eval.run_mcq_product
"""

import csv
import sys
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

# Avoid UnicodeEncodeError on Windows consoles (cp1252) when LLM
# output contains characters like '≥', '°', etc.
sys.stdout.reconfigure(
    encoding="utf-8",
    errors="replace",
)

from terramind.rag.product.generate import (
    format_context,
    create_llm,
)

from terramind.rag.product.config import (
    RAG_PROMPT,
)

from terramind.rag.product.hybrid import (
    hybrid_retrieve,
)

from terramind.rag.product.rerank import (
    rerank_chunks,
)

from terramind.rag.product.rewrite import (
    rewrite_query,
)

from terramind.rag.product.store import (
    load_vector_store,
)

from terramind.FullEvaluation.evaluate import (
    REPORTS_DIR,
)

from terramind.FullEvaluation.metrics.metrics import (
    clean_answer,
)

from terramind.FullEvaluation.heuristic_eval.run_mcq_general import (
    extract_letter,
    save_report,
)


MCQ_PRODUCT_CSV_PATH = (
    Path(__file__).resolve().parent
    / "mcq_product.csv"
)


def load_mcq_dataset(path: Path = MCQ_PRODUCT_CSV_PATH) -> list:

    with open(
        path,
        "r",
        encoding="utf-8",
    ) as f:

        return list(csv.DictReader(f))


def build_mcq_prompt(row: dict) -> str:

    return (
        f"{row['question']}\n"
        f"A) {row['A']}\n"
        f"B) {row['B']}\n"
        f"C) {row['C']}\n"
        f"D) {row['D']}\n\n"
        "MULTIPLE-CHOICE QUESTION — IGNORE ALL FORMATTING/STYLE RULES "
        "ABOVE (no headings, no bullets, no sources section, no "
        "explanation). Respond with ONLY the single letter of the "
        "correct option: A, B, C, or D. No words, no punctuation, "
        "no explanation — just the one letter."
    )


def generate_mcq_answer(
    db,
    question: str,
    mcq_prompt: str,
) -> str:
    """
    Retrieve using the bare question (so rewrite_query/hybrid_retrieve
    see a clean retrieval signal), but generate using the MCQ-augmented
    prompt so the LLM is instructed to answer with a single letter.
    """

    retrieval_query = rewrite_query(
        question
    )

    candidates = hybrid_retrieve(
        db,
        retrieval_query,
        k=8,
    )

    chunks = rerank_chunks(
        question,
        candidates,
        top_k=3,
    )

    if not chunks:

        return (
            "I could not find relevant "
            "information in the product catalog."
        )

    context = format_context(
        chunks
    )

    prompt = RAG_PROMPT.format(
        context=context,
        question=mcq_prompt,
    )

    llm = create_llm()

    response = llm.invoke(
        prompt
    )

    return response.content


def run_mcq_product():

    db = load_vector_store()

    test_cases = load_mcq_dataset()

    total = len(test_cases)

    detailed_results = []

    report_path = (
        REPORTS_DIR
        / "mcq_product_report.json"
    )

    for i, row in enumerate(test_cases, start=1):

        question = row["question"]

        expected = row["expected_answer"].strip().upper()

        prompt = build_mcq_prompt(row)

        print(
            "\n" + "=" * 80
        )

        print(
            f"[{i}/{total}] {question}"
        )

        try:

            raw_answer = generate_mcq_answer(
                db,
                question,
                prompt,
            )

            cleaned = clean_answer(
                raw_answer
            )

            predicted = extract_letter(
                cleaned
            )

            correct = predicted == expected

            print(
                f"Expected: {expected}  Predicted: {predicted}  "
                f"{'OK' if correct else 'WRONG'}"
            )

            print(
                f"Raw answer: {cleaned}"
            )

            detailed_results.append(
                {
                    "id": row.get("id"),
                    "product_id": row.get("product_id"),
                    "question": question,
                    "category": row.get("category"),
                    "expected_answer": expected,
                    "predicted_answer": predicted,
                    "raw_answer": cleaned,
                    "correct": correct,
                }
            )

        except Exception as exc:

            print(
                f"ERROR on question {i}: {exc}"
            )

            detailed_results.append(
                {
                    "id": row.get("id"),
                    "product_id": row.get("product_id"),
                    "question": question,
                    "category": row.get("category"),
                    "expected_answer": expected,
                    "error": str(exc),
                    "correct": None,
                }
            )

        save_report(
            report_path,
            detailed_results,
            total,
        )

    accuracy = save_report(
        report_path,
        detailed_results,
        total,
    )

    print(
        "\n" + "=" * 80
    )

    print(
        f"Accuracy: {accuracy:.3f}"
    )

    print(
        f"Total questions evaluated: {total}"
    )

    print(
        f"\nReport saved to:\n{report_path}"
    )


if __name__ == "__main__":
    run_mcq_product()
