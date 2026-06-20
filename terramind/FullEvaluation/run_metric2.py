"""
Run Metric 2 (Factual Correctness) over Product RAG, using
golden_product_rag.jsonl.

For each question:
    - generate a real RAG answer (generate_answer)
    - decompose golden + generated answers into atomic claims
    - verify claim overlap in both directions
    - compute precision, recall, F1

Saves a detailed report to reports/metric2_report_product_optimized.json.

Run:
    python -m terramind.FullEvaluation.run_metric2
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

from terramind.rag.product.generate import (
    generate_answer,
)

from terramind.rag.product.store import (
    load_vector_store,
)

from terramind.FullEvaluation.evaluate import (
    load_product_dataset,
    REPORTS_DIR,
)

from terramind.FullEvaluation.metrics.metrics import (
    clean_answer,
    decompose_claims,
    verify_claims,
)


def factual_correctness_detailed(
    golden: str,
    generated: str,
) -> dict:
    """
    Same logic as factual_correctness_score,
    but returns the full breakdown for reporting.
    """

    golden_claims = decompose_claims(
        golden
    )

    generated_claims = decompose_claims(
        generated
    )

    if not golden_claims and not generated_claims:

        return {
            "golden_claims": [],
            "generated_claims": [],
            "precision": 1.0,
            "recall": 1.0,
            "f1": 1.0,
        }

    if not golden_claims or not generated_claims:

        return {
            "golden_claims": golden_claims,
            "generated_claims": generated_claims,
            "precision": 0.0,
            "recall": 0.0,
            "f1": 0.0,
        }

    precision_hits = verify_claims(
        generated_claims,
        golden,
    )

    recall_hits = verify_claims(
        golden_claims,
        generated,
    )

    precision = (
        precision_hits
        / len(generated_claims)
    )

    recall = (
        recall_hits
        / len(golden_claims)
    )

    if precision + recall == 0:
        f1 = 0.0

    else:
        f1 = (
            2 * precision * recall
            / (precision + recall)
        )

    return {
        "golden_claims": golden_claims,
        "generated_claims": generated_claims,
        "precision": precision,
        "recall": recall,
        "f1": f1,
    }


def save_report(
    report_path: Path,
    detailed_results: list,
    total: int,
):

    f1_scores = [
        r["f1"]
        for r in detailed_results
        if r.get("f1") is not None
    ]

    average_f1 = (
        sum(f1_scores) / len(f1_scores)
        if f1_scores
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
                    "average_factual_correctness": average_f1,
                    "questions_completed": len(detailed_results),
                    "total_questions": total,
                },
                "results": detailed_results,
            },
            f,
            indent=4,
            ensure_ascii=False,
        )

    return average_f1


def run_metric2():

    db = load_vector_store()

    test_cases = load_product_dataset()

    total = len(test_cases)

    detailed_results = []

    report_path = (
        REPORTS_DIR
        / "metric2_report_product_optimized.json"
    )

    for i, test in enumerate(test_cases, start=1):

        question = test.get("question")

        golden = test.get(
            "golden",
            test.get("reference_answer"),
        )

        print(
            "\n" + "=" * 80
        )

        print(
            f"[{i}/{total}] Question: {question}"
        )

        try:

            answer = generate_answer(
                db,
                question,
            )

            generated = clean_answer(
                answer
            )

            print(
                f"Golden:    {golden}"
            )

            print(
                f"Generated: {generated}"
            )

            result = factual_correctness_detailed(
                golden,
                generated,
            )

            print(
                f"Golden claims:    {result['golden_claims']}"
            )

            print(
                f"Generated claims: {result['generated_claims']}"
            )

            print(
                f"Precision: {result['precision']:.3f}  "
                f"Recall: {result['recall']:.3f}  "
                f"F1: {result['f1']:.3f}"
            )

            detailed_results.append(
                {
                    "question": question,
                    "golden": golden,
                    "generated": generated,
                    **result,
                }
            )

        except Exception as exc:

            print(
                f"ERROR on question {i}: {exc}"
            )

            detailed_results.append(
                {
                    "question": question,
                    "golden": golden,
                    "error": str(exc),
                    "f1": None,
                }
            )

        # Save progress after every question so a
        # crash doesn't lose completed work.
        save_report(
            report_path,
            detailed_results,
            total,
        )

    average_f1 = save_report(
        report_path,
        detailed_results,
        total,
    )

    print(
        "\n" + "=" * 80
    )

    print(
        f"Average Factual Correctness (F1): {average_f1:.3f}"
    )

    print(
        f"Total questions evaluated: {total}"
    )

    print(
        f"\nReport saved to:\n{report_path}"
    )


if __name__ == "__main__":
    run_metric2()
