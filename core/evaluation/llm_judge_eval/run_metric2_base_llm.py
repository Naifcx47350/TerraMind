"""
Run Metric 2 (Factual Correctness) over the base LLM (Mode 3, no retrieval),
on the full golden dataset (general + product).

Same Metric 2 logic as run_metric2.py / run_metric2_general.py, but answers
come from core.models.base_llm (plain gpt-4o-mini, no catalog or
document retrieval).

Saves:
    reports/metric2_base_llm_golden_report.json

Run:
    python -m core.evaluation.llm_judge_eval.run_metric2_base_llm
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

from core.models.base_llm import (
    answer as base_llm_answer,
)

from core.evaluation.evaluate import (
    load_dataset,
    REPORTS_DIR,
)

from core.evaluation.metrics.metrics import (
    clean_answer,
)

from core.evaluation.llm_judge_eval.run_metric2 import (
    factual_correctness_detailed,
)

from core.evaluation.llm_judge_eval.run_metric2_general import (
    save_report,
)


def run_metric2_base_llm():

    def answer_with_base_llm(_db, question):
        result = base_llm_answer(question)
        return {"answer": result["answer"]}

    golden_cases = load_dataset()

    _run(
        golden_cases,
        get_question=lambda t: t.get("question"),
        get_golden=lambda t: t.get(
            "golden",
            t.get("reference_answer"),
        ),
        extra_fields=lambda t: {
            "category": t.get("category"),
        },
        report_path=REPORTS_DIR / "metric2_base_llm_golden_report.json",
        label="GOLDEN",
        answer_fn=answer_with_base_llm,
    )


def _run(
    test_cases: list,
    get_question,
    get_golden,
    extra_fields,
    report_path: Path,
    label: str,
    answer_fn,
):

    total = len(test_cases)

    detailed_results = []

    for i, test in enumerate(test_cases, start=1):

        question = get_question(test)

        golden = get_golden(test)

        print(
            "\n" + "=" * 80
        )

        print(
            f"[{label} {i}/{total}] Question: {question}"
        )

        try:

            result_dict = answer_fn(
                None,
                question,
            )

            generated = clean_answer(
                result_dict["answer"]
            )

            print(
                f"Golden:    {golden}"
            )

            print(
                f"Generated: {generated}"
            )

            metric = factual_correctness_detailed(
                golden,
                generated,
            )

            print(
                f"Golden claims:    {metric['golden_claims']}"
            )

            print(
                f"Generated claims: {metric['generated_claims']}"
            )

            print(
                f"Precision: {metric['precision']:.3f}  "
                f"Recall: {metric['recall']:.3f}  "
                f"F1: {metric['f1']:.3f}"
            )

            detailed_results.append(
                {
                    **extra_fields(test),
                    "question": question,
                    "golden": golden,
                    "generated": generated,
                    **metric,
                }
            )

        except Exception as exc:

            print(
                f"ERROR on {label} question {i}: {exc}"
            )

            detailed_results.append(
                {
                    **extra_fields(test),
                    "question": question,
                    "golden": golden,
                    "error": str(exc),
                    "f1": None,
                }
            )

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
        f"[{label}] Average Factual Correctness (F1): {average_f1:.3f}"
    )

    print(
        f"[{label}] Total questions evaluated: {total}"
    )

    print(
        f"[{label}] Report saved to:\n{report_path}"
    )


if __name__ == "__main__":
    run_metric2_base_llm()
