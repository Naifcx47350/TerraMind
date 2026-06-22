"""
Run Metric 1 (Faithfulness, via LLM judge) and Metric 3 (Semantic
Similarity) over Product RAG, using golden_product_rag.jsonl.

Saves detailed reports to reports/metric1_report_product_optimized.json
and reports/metric3_report_product_optimized.json.

Run:
    python -m core.evaluation.llm_judge_eval.run_metric1_3
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

from core.rag.product.generate import (
    generate_answer_with_metadata,
    format_context,
)

from core.rag.product.store import (
    load_vector_store,
)

from core.evaluation.evaluate import (
    load_product_dataset,
    REPORTS_DIR,
)

from core.evaluation.metrics.metrics import (
    clean_answer,
    coverage_judge_score,
)

from core.evaluation.metrics.llm_judge import (
    judge_answer,
)


def save_report(
    metric1_path: Path,
    metric3_path: Path,
    detailed_results: list,
    total: int,
):

    similarity_results = [
        {
            "question": r["question"],
            "golden": r["golden"],
            "generated": r.get("generated"),
            "similarity": r.get("similarity"),
        }
        for r in detailed_results
    ]

    faithfulness_results = [
        {
            "question": r["question"],
            "golden": r["golden"],
            "generated": r.get("generated"),
            "judge": r.get("judge"),
        }
        for r in detailed_results
    ]

    similarity_scores = [
        r["similarity"]
        for r in detailed_results
        if r.get("similarity") is not None
    ]

    faithfulness_scores = [
        r["judge"]["faithfulness"]
        for r in detailed_results
        if r.get("judge")
    ]

    average_similarity = (
        sum(similarity_scores) / len(similarity_scores)
        if similarity_scores
        else 0.0
    )

    average_faithfulness = (
        sum(faithfulness_scores) / len(faithfulness_scores)
        if faithfulness_scores
        else 0.0
    )

    with open(
        metric3_path,
        "w",
        encoding="utf-8",
    ) as f:

        json.dump(
            {
                "summary": {
                    "average_similarity": average_similarity,
                    "questions_completed": len(detailed_results),
                    "total_questions": total,
                },
                "results": similarity_results,
            },
            f,
            indent=4,
            ensure_ascii=False,
        )

    with open(
        metric1_path,
        "w",
        encoding="utf-8",
    ) as f:

        json.dump(
            {
                "summary": {
                    "average_faithfulness": average_faithfulness,
                    "questions_completed": len(detailed_results),
                    "total_questions": total,
                },
                "results": faithfulness_results,
            },
            f,
            indent=4,
            ensure_ascii=False,
        )

    return average_similarity, average_faithfulness


def run_metric1_3():

    db = load_vector_store()

    test_cases = load_product_dataset()

    total = len(test_cases)

    detailed_results = []

    metric1_path = (
        REPORTS_DIR
        / "metric1_report_product_optimized.json"
    )

    metric3_path = (
        REPORTS_DIR
        / "metric3_report_product_optimized.json"
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

            result = generate_answer_with_metadata(
                db,
                question,
            )

            generated = clean_answer(
                result["answer"]
            )

            context = format_context(
                result["retrieved"]
            )

            print(
                f"Golden:    {golden}"
            )

            print(
                f"Generated: {generated}"
            )

            similarity = coverage_judge_score(
                golden,
                generated,
            )["coverage"]

            judge = judge_answer(
                question,
                context,
                golden,
                generated,
            )

            print(
                f"Similarity: {similarity:.3f}  "
                f"Faithfulness: {judge['faithfulness']:.3f}"
            )

            detailed_results.append(
                {
                    "question": question,
                    "golden": golden,
                    "generated": generated,
                    "similarity": similarity,
                    "judge": judge,
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
                    "similarity": None,
                    "judge": None,
                }
            )

        # Save progress after every question so a
        # crash doesn't lose completed work.
        save_report(
            metric1_path,
            metric3_path,
            detailed_results,
            total,
        )

    average_similarity, average_faithfulness = save_report(
        metric1_path,
        metric3_path,
        detailed_results,
        total,
    )

    print(
        "\n" + "=" * 80
    )

    print(
        f"Average Semantic Similarity: {average_similarity:.3f}"
    )

    print(
        f"Average Faithfulness: {average_faithfulness:.3f}"
    )

    print(
        f"Total questions evaluated: {total}"
    )

    print(
        f"\nReports saved to:\n{metric1_path}\n{metric3_path}"
    )


if __name__ == "__main__":
    run_metric1_3()
