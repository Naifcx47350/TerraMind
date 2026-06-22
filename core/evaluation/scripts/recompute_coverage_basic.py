"""
Recomputes coverage_judge_score over the golden/generated pairs already
saved in metric3_report_product_basic.json (the Basic Product RAG
version, before hybrid retrieval/rerank/query rewrite). Does not
regenerate answers — just replaces the old cosine score with the new
LLM-judge score on the same text.

Run:
    python -m core.evaluation.scripts.recompute_coverage_basic
"""
import sys
import json
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from core.evaluation.metrics.metrics import coverage_judge_score
from core.evaluation.evaluate import REPORTS_DIR


def recompute_coverage_basic():

    report_path = REPORTS_DIR / "metric3_report_product_basic.json"

    with open(report_path, encoding="utf-8") as f:
        data = json.load(f)

    results = data["results"]
    total = len(results)

    for i, r in enumerate(results, start=1):

        print(f"[{i}/{total}] {r['question']}")

        judge = coverage_judge_score(
            r["golden"],
            r["generated"],
        )

        r["old_similarity"] = r.get("similarity")
        r["similarity"] = judge["coverage"]
        r["coverage_reasoning"] = judge["reasoning"]

        print(
            f"  old: {r['old_similarity']:.3f}  "
            f"coverage_judge: {judge['coverage']:.3f}"
        )

        with open(report_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)

    scores = [r["similarity"] for r in results if r.get("similarity") is not None]

    average_coverage = sum(scores) / len(scores) if scores else 0.0

    data["summary"]["average_old_similarity"] = data["summary"].get(
        "average_similarity"
    )
    data["summary"]["average_similarity"] = average_coverage

    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

    print("\n" + "=" * 70)
    print(f"Average coverage_judge (Basic Product RAG): {average_coverage:.3f}")
    print(f"Report updated: {report_path}")


if __name__ == "__main__":
    recompute_coverage_basic()
