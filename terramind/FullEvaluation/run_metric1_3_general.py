"""
Run Metric 1 (Faithfulness, via LLM judge) and Metric 3 (Semantic
Similarity) over General RAG, using golden_general_rag.jsonl.

Saves detailed reports to reports/metric1_report_general.json
and reports/metric3_report_general.json.

Run:
    python -m terramind.FullEvaluation.run_metric1_3_general
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

from terramind.rag.general.pipeline import (
    get_general_db,
    answer_with_rag,
)

from terramind.FullEvaluation.evaluate import (
    load_general_dataset,
    REPORTS_DIR,
)

from terramind.FullEvaluation.metrics.metrics import (
    clean_answer,
    similarity_score,
)

from terramind.FullEvaluation.metrics.llm_judge import (
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
            "id": r.get("id"),
            "category": r.get("category"),
            "question": r["question"],
            "golden": r["golden"],
            "generated": r.get("generated"),
            "similarity": r.get("similarity"),
        }
        for r in detailed_results
    ]

    faithfulness_results = [
        {
            "id": r.get("id"),
            "category": r.get("category"),
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


def run_metric1_3_general():

    print("Loading General RAG index...")

    db = get_general_db()

    test_cases = load_general_dataset()

    total = len(test_cases)

    detailed_results = []

    metric1_path = (
        REPORTS_DIR
        / "metric1_report_general.json"
    )

    metric3_path = (
        REPORTS_DIR
        / "metric3_report_general.json"
    )

    for i, test in enumerate(test_cases, start=1):

        question = test.get("question")

        golden = test.get("golden")

        print(
            "\n" + "=" * 80
        )

        print(
            f"[GENERAL {i}/{total}] Question: {question}"
        )

        try:

            result = answer_with_rag(
                db,
                question,
            )

            generated = clean_answer(
                result["answer"]
            )

            print(
                f"Golden:    {golden}"
            )

            print(
                f"Generated: {generated}"
            )

            similarity = similarity_score(
                golden,
                generated,
            )

            judge = judge_answer(
                question,
                result["context"],
                golden,
                generated,
            )

            print(
                f"Similarity: {similarity:.3f}  "
                f"Faithfulness: {judge['faithfulness']:.3f}"
            )

            detailed_results.append(
                {
                    "id": test.get("id"),
                    "category": test.get("category"),
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
                    "id": test.get("id"),
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
        f"[GENERAL] Average Semantic Similarity: {average_similarity:.3f}"
    )

    print(
        f"[GENERAL] Average Faithfulness: {average_faithfulness:.3f}"
    )

    print(
        f"[GENERAL] Total questions evaluated: {total}"
    )

    print(
        f"\nReports saved to:\n{metric1_path}\n{metric3_path}"
    )


if __name__ == "__main__":
    run_metric1_3_general()
