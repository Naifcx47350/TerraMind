import json
from pathlib import Path

from terramind.rag.product.generate import (
    generate_answer,
)

from terramind.FullEvaluation.metrics.metrics import (
    normalize,
    clean_answer,
    similarity_score,
    agri_score,
)


BASE_DIR = Path(__file__).resolve().parent

DATASET_PATH = (
    BASE_DIR /
    "datasets" /
    # "Golden_Data_Client_after-Carlo.json"
    "golden_dataset.json"
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


def run_evaluation():

    test_cases = load_dataset()

    scores = []

    agri_scores = []

    passed = 0

    detailed_results = []

    for test in test_cases:

        print(
            "\n" + "=" * 80
        )

        question = test.get("question")

        golden = test.get("golden", test.get("reference_answer"))

        # Check both capitalized and lowercase column names
        # question = test.get("Question", test.get("question"))
        # golden = test.get("Golden Answer", test.get("golden", test.get("reference_answer")))

        print(
            f"Question: {question}"
        )

        print(
            f"Golden: {golden}"
        )

        answer = generate_answer(
            question
        )

        generated = clean_answer(
            answer
        )

        contains_golden = (
            normalize(
                golden
            )
            in
            normalize(
                generated
            )
        )

        if contains_golden:

            passed += 1

        similarity = similarity_score(
            golden,
            generated,
        )

        agricultural_accuracy = (
            agri_score(
                golden,
                generated,
            )
        )

        scores.append(
            similarity
        )

        agri_scores.append(
            agricultural_accuracy
        )

        print(
            f"\nGenerated:\n"
            f"{generated}"
        )

        print(
            f"\nContains Golden: "
            f"{contains_golden}"
        )

        print(
            f"Similarity: "
            f"{similarity:.3f}"
        )

        print(
            f"Agricultural Accuracy: "
            f"{agricultural_accuracy:.3f}"
        )

        detailed_results.append(
            {
                "question": question,
                "golden": golden,
                "generated": generated,
                "contains_golden": contains_golden,
                "similarity": similarity,
                "agricultural_accuracy": agricultural_accuracy,
            }
        )

    average_similarity = (
        sum(scores) /
        len(scores)
    )

    average_agri_accuracy = (
        sum(agri_scores) /
        len(agri_scores)
    )

    pass_rate = (
        passed /
        len(test_cases)
    ) * 100

    print(
        "\n" + "=" * 80
    )

    print(
        f"Average Similarity: "
        f"{average_similarity:.3f}"
    )

    print(
        f"Average Agricultural Accuracy: "
        f"{average_agri_accuracy:.3f}"
    )

    print(
        f"Pass Rate: "
        f"{pass_rate:.1f}%"
    )

    summary = {
        "average_similarity":
            average_similarity,
        "average_agricultural_accuracy":
            average_agri_accuracy,
        "pass_rate":
            pass_rate,
        "total_questions":
            len(test_cases),
    }

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