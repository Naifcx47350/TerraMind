"""
Smoke test for Metric 2: Factual Correctness.

Runs decompose_claims / verify_claims / factual_correctness_score
on a few small examples so we can sanity-check the LLM prompts and
JSON parsing before running the full benchmark.

Run:
    python -m core.evaluation.test_metric2
"""

from dotenv import load_dotenv

load_dotenv()

from core.evaluation.metrics.metrics import (
    decompose_claims,
    verify_claims,
    factual_correctness_score,
)


EXAMPLES = [
    {
        "name": "Partial match (application count differs)",
        "golden": "Spray every 21 days. Apply 1 time per season.",
        "generated": "Spray every 21 days. Apply 2 times per season.",
    },
    {
        "name": "Exact match (different wording)",
        "golden": "Mix 30g of the agent with 30 jin of water and apply once.",
        "generated": "Mix 30 grams of the agent into 30 jin of water and apply it one time.",
    },
    {
        "name": "No overlap",
        "golden": "The safety interval is 21 days.",
        "generated": "The product comes in a 500g bag.",
    },
]


def main():

    for example in EXAMPLES:

        print("\n" + "=" * 80)
        print(example["name"])
        print("-" * 80)

        print(f"Golden:    {example['golden']}")
        print(f"Generated: {example['generated']}")

        golden_claims = decompose_claims(
            example["golden"]
        )

        generated_claims = decompose_claims(
            example["generated"]
        )

        print(f"\nGolden claims:    {golden_claims}")
        print(f"Generated claims: {generated_claims}")

        precision_hits = verify_claims(
            generated_claims,
            example["golden"],
        )

        recall_hits = verify_claims(
            golden_claims,
            example["generated"],
        )

        print(
            f"\nPrecision hits: {precision_hits}/{len(generated_claims)}"
        )

        print(
            f"Recall hits:    {recall_hits}/{len(golden_claims)}"
        )

        score = factual_correctness_score(
            example["golden"],
            example["generated"],
        )

        print(f"\nFactual Correctness (F1): {score:.3f}")


if __name__ == "__main__":
    main()
