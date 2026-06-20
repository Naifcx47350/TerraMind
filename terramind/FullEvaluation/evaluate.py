import json
from pathlib import Path

from terramind.rag.product.generate import (
    generate_answer_with_metadata,
    format_context,
)

from terramind.rag.product.store import (
    load_vector_store,
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

GENERAL_DATASET_PATH = (
    BASE_DIR /
    "datasets" /
    "golden_general_rag.jsonl"
)

PRODUCT_DATASET_PATH = (
    BASE_DIR /
    "datasets" /
    "golden_product_rag.jsonl"
)

REPORTS_DIR = (
    BASE_DIR /
    "reports"
)

REPORTS_DIR.mkdir(
    exist_ok=True
)


def _load_jsonl(path: Path) -> list:
    """
    Load test cases from a JSONL file (one JSON object per line),
    normalizing "golden_answer" into a "golden" key.
    """

    test_cases = []

    with open(
        path,
        "r",
        encoding="utf-8",
    ) as f:

        for line in f:

            line = line.strip()

            if not line:
                continue

            test = json.loads(line)

            test.setdefault(
                "golden",
                test.get("golden_answer"),
            )

            test_cases.append(test)

    return test_cases


def load_general_dataset():
    """
    Load the General RAG benchmark question set.
    """

    return _load_jsonl(GENERAL_DATASET_PATH)


def load_product_dataset():
    """
    Load the Product RAG benchmark question set.
    """

    return _load_jsonl(PRODUCT_DATASET_PATH)


def load_dataset():
    """
    Load the full benchmark question set
    (general + product combined).
    """

    return load_general_dataset() + load_product_dataset()


def relevant_product_id(test: dict) -> str | None:
    """
    Ground-truth product ID for retrieval metrics,
    read directly from the "product_id" field.
    """

    return test.get("product_id")


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

    db = load_vector_store()

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

        question = test.get("question")

        golden = test.get("golden")

        product_id = relevant_product_id(test)

        print(
            f"Question: {question}"
        )

        print(
            f"Golden: {golden}"
        )

        result = generate_answer_with_metadata(
            db,
            question,
        )

        answer = result["answer"]

        chunks = result["retrieved"]

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
