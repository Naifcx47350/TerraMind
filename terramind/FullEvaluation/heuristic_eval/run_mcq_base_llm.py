"""
Run a multiple-choice (MCQ) evaluation over the Base LLM (Mode 3, no
retrieval), using mcq_general.csv.

Same logic as run_mcq_general.py, but answers come from
terramind.models.base_llm (plain gpt-4o-mini, no catalog or document
retrieval) instead of the General RAG.

Saves a detailed report to reports/mcq_base_llm_report.json.

Run:
    python -m terramind.FullEvaluation.heuristic_eval.run_mcq_base_llm
"""

import json
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

from terramind.models.base_llm import (
    answer as base_llm_answer,
)

from terramind.FullEvaluation.evaluate import (
    REPORTS_DIR,
)

from terramind.FullEvaluation.heuristic_eval.run_mcq_general import (
    MCQ_CSV_PATH,
    load_mcq_dataset,
    build_mcq_prompt,
    extract_letter,
    save_report,
)


def run_mcq_base_llm():

    test_cases = load_mcq_dataset(MCQ_CSV_PATH)

    total = len(test_cases)

    detailed_results = []

    report_path = (
        REPORTS_DIR
        / "mcq_base_llm_report.json"
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

            result = base_llm_answer(
                prompt
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
    run_mcq_base_llm()
