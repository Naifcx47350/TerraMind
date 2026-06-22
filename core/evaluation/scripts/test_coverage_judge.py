"""
Tests coverage_judge_score on just 4 questions: G012, G013, G014, G045.

Expected:
- G014 drops (content diverges from golden)
- G045, G012, G013 rise above 0.7 (correct content covered, just longer/differently organized)

Run:
    python -m core.evaluation.test_coverage_judge
"""
import sys
import json

from dotenv import load_dotenv

load_dotenv()

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from core.evaluation.metrics.metrics import coverage_judge_score


with open(
    "core/evaluation/reports/metric3_report_general.json",
    encoding="utf-8",
) as f:
    data = json.load(f)

target_ids = {"G012", "G013", "G014", "G045"}

for r in data["results"]:
    if r.get("id") not in target_ids:
        continue

    result = coverage_judge_score(r["golden"], r["generated"])

    print("=" * 70)
    print(f"[{r['id']}]  old similarity: {r.get('similarity'):.3f}")
    print(f"  coverage_judge: {result['coverage']:.3f}")
    print(f"  reasoning: {result['reasoning']}")

print("=" * 70)
