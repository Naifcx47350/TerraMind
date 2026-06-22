"""
Run a multiple-choice (MCQ) evaluation over the General RAG, using
mcq_general.csv.

For each row:
    - retrieve context using the bare question
    - ask the General RAG to answer with a single letter (A/B/C/D)
    - compare the extracted letter to expected_answer

Saves a detailed report to reports/mcq_general_report.json.

Run:
    python -m core.evaluation.heuristic_eval.run_mcq_general
"""

import csv
import json
import re
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

from core.rag.general.pipeline import (
    get_general_db,
    answer_with_rag,
)

from core.evaluation.evaluate import (
    REPORTS_DIR,
)


MCQ_CSV_PATH = (
    Path(__file__).resolve().parent
    / "mcq_general.csv"
)


def load_mcq_dataset(path: Path = MCQ_CSV_PATH) -> list:

    with open(
        path,
        "r",
        encoding="utf-8",
    ) as f:

        return list(csv.DictReader(f))


def build_mcq_prompt(row: dict) -> str:

    return (
        "MULTIPLE-CHOICE QUESTION — IGNORE ALL FORMATTING/STYLE RULES "
        "ABOVE (no headings, no bullets, no citations, no explanation).\n"
        f"{row['question']}\n"
        f"A) {row['A']}\n"
        f"B) {row['B']}\n"
        f"C) {row['C']}\n"
        f"D) {row['D']}\n\n"
        "Respond with ONLY the single letter of the correct option: "
        "A, B, C, or D. No words, no punctuation, no explanation — "
        "just the one letter."
    )


def extract_letter(text: str) -> str | None:
    """
    Extract a single A/B/C/D answer letter from model output.

    Only matches a letter immediately followed by a typical MCQ
    delimiter (end of string, punctuation, or "answer is/option ___"
    phrasing) so that plain English words like "a"/"i" in a refusal
    sentence are never mistaken for the chosen option.
    """

    cleaned = text.strip().upper()
    cleaned = re.sub(r"[*_`]", "", cleaned)

    match = re.fullmatch(
        r"[^A-D]*\(?([ABCD])\)?[.:]?",
        cleaned,
    )

    if match:
        return match.group(1)

    match = re.search(
        r"(?:ANSWER|OPTION|CHOICE)\s*(?:IS|:)?\s*\(?([ABCD])\)?\b",
        cleaned,
    )

    return match.group(1) if match else None


def save_report(
    report_path: Path,
    detailed_results: list,
    total: int,
):

    scored = [
        r
        for r in detailed_results
        if r.get("correct") is not None
    ]

    correct_count = sum(
        1
        for r in scored
        if r["correct"]
    )

    accuracy = (
        correct_count / len(scored)
        if scored
        else 0.0
    )

    with open(
        report_path,
        "w",
        encoding="utf-8",
    ) as f:

        json.dump(
            {
                "summary": {
                    "accuracy": accuracy,
                    "correct": correct_count,
                    "questions_completed": len(detailed_results),
                    "total_questions": total,
                },
                "results": detailed_results,
            },
            f,
            indent=4,
            ensure_ascii=False,
        )

    return accuracy


def run_mcq_general():

    print("Loading General RAG index...")

    db = get_general_db()

    test_cases = load_mcq_dataset()

    total = len(test_cases)

    detailed_results = []

    report_path = (
        REPORTS_DIR
        / "mcq_general_report.json"
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

            result = answer_with_rag(
                db,
                question,
                generation_prompt=prompt,
            )

            raw_answer = result["answer"]

            predicted = extract_letter(
                raw_answer
            )

            correct = predicted == expected

            print(
                f"Expected: {expected}  Predicted: {predicted}  "
                f"{'OK' if correct else 'WRONG'}"
            )

            print(
                f"Raw answer: {raw_answer}"
            )

            detailed_results.append(
                {
                    "id": row.get("id"),
                    "question": question,
                    "category": row.get("category"),
                    "expected_answer": expected,
                    "predicted_answer": predicted,
                    "raw_answer": raw_answer,
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
    run_mcq_general()
