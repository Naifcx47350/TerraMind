import json
from pathlib import Path

from terramind.rag.product.generate import (
    generate_answer_with_chunks,
    format_context,
)

from terramind.FullEvaluation.metrics.metrics import (
    clean_answer,
    similarity_score,
    agri_score,
    is_refusal,
)

from terramind.FullEvaluation.metrics.retrieval_metrics import (
    retrieval_metrics,
)

from terramind.FullEvaluation.metrics.llm_judge import (
    judge_answer,
)


BASE_DIR = Path(__file__).resolve().parent

DATASET_PATH = (
    BASE_DIR /
    "datasets" /
    "Golden_Data_Client_after-Carlo.json"
)

REPORTS_DIR = (
    BASE_DIR /
    "reports"
)

REPORTS_DIR.mkdir(
    exist_ok=True
)


def load_dataset():
    """
    Load benchmark questions.
    """

    with open(
        DATASET_PATH,
        "r",
        encoding="utf-8",
    ) as f:

        return json.load(
            f
        )


def relevant_product_id(test: dict) -> str | None:
    """
    Extract the ground-truth product ID from the
    "Source (catalog)" field, e.g. "PN0005 29%..." -> "PN0005".
    """

    source = test.get("Source (catalog)")

    if not source:
        return None

    return source.strip().split()[0]


def average(dicts: list[dict]) -> dict:
    """
    Average each numeric field across a
    list of same-shaped dicts.
    """

    if not dicts:
        return {}

    keys = dicts[0].keys()

    return {
        key: sum(d[key] for d in dicts) / len(dicts)
        for key in keys
    }


def run_evaluation():

    test_cases = load_dataset()

    detailed_results = []

    quality_scores = []
    retrieval_scores = []
    judge_scores = []
    refusals = []

    for test in test_cases:

        print(
            "\n" + "=" * 80
        )

        question = test.get("Question")

        golden = test.get("Golden Answer")

        product_id = relevant_product_id(test)

        print(
            f"Question: {question}"
        )

        print(
            f"Golden: {golden}"
        )

        answer, chunks = generate_answer_with_chunks(
            question
        )

        generated = clean_answer(
            answer
        )

        context = format_context(
            chunks
        )

        similarity = similarity_score(
            golden,
            generated,
        )

        agricultural_accuracy = agri_score(
            golden,
            generated,
        )

        refused = is_refusal(
            generated
        )

        retrieval = (
            retrieval_metrics(chunks, product_id)
            if product_id
            else None
        )

        judge = judge_answer(
            question,
            context,
            golden,
            generated,
        )

        quality = {
            "similarity": similarity,
            "agricultural_accuracy": agricultural_accuracy,
        }

        quality_scores.append(quality)
        judge_scores.append(judge)
        refusals.append(refused)

        if retrieval is not None:
            retrieval_scores.append(retrieval)

        print(
            f"\nGenerated:\n"
            f"{generated}"
        )

        print(
            f"Similarity: {similarity:.3f}"
        )

        print(
            f"Agricultural Accuracy: {agricultural_accuracy:.3f}"
        )

        if retrieval is not None:
            print(
                f"Retrieval: {retrieval}"
            )

        print(
            f"Judge: {judge}"
        )

        detailed_results.append(
            {
                "question": question,
                "golden": golden,
                "generated": generated,
                "relevant_product_id": product_id,
                "refused": refused,
                **quality,
                "retrieval": retrieval,
                "judge": judge,
            }
        )

    summary = {
        "total_questions": len(test_cases),
        "refusal_rate": sum(refusals) / len(refusals),
        **average(quality_scores),
        "retrieval": average(retrieval_scores),
        "judge": average(judge_scores),
    }

    print(
        "\n" + "=" * 80
    )

    print(
        json.dumps(summary, indent=2)
    )

    with open(
        REPORTS_DIR /
        "benchmark_report2.json",
        "w",
        encoding="utf-8",
    ) as f:

        json.dump(
            {
                "summary":
                    summary,
                "results":
                    detailed_results,
            },
            f,
            indent=4,
            ensure_ascii=False,
        )

    print(
        f"\nReport saved to:\n"
        f"{REPORTS_DIR / 'benchmark_report2.json'}"
    )


if __name__ == "__main__":

    run_evaluation()
