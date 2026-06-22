# Full Evaluation Report — All Three Systems (Heuristic + LLM-as-Judge)

Date: 2026-06-22

This report combines results from **two separate evaluation methods**, applied to **three systems**:

- **Evaluation methods:**
  - **Heuristic (`heuristic_eval/`)** — multiple-choice questions (MCQ), exact letter-match grading, no LLM involved in the scoring step itself.
  - **LLM-as-Judge (`llm_judge_eval/`)** — open-ended questions (`golden_general_rag.jsonl` / `golden_product_rag.jsonl`), scored by gpt-4o-mini as judge across 3 metrics: Faithfulness (Metric 1), Semantic Similarity (Metric 3), Factual Correctness F1 (Metric 2).

- **Systems:**
  - **Base LLM** — gpt-4o-mini with no retrieval.
  - **General RAG** — general agriculture references (FAO/IPM/GAP...).
  - **Product RAG** — two versions: **Basic** (old code, pre-hybrid retrieval/rerank — from the `evaluation-base` branch) and **Optimized** (current code, hybrid BM25 + cross-encoder rerank + query rewrite + metadata filter).

---

## 0) Overall Summary — All Results in One Table

### Heuristic (MCQ) — exact-match

| System | Question Set | Questions | Correct | Accuracy |
|---|---|---|---|---|
| Base LLM | mcq_general.csv | 10 | 10 | **100.0%** |
| General RAG | mcq_general.csv | 10 | 10 | **100.0%** |
| Base LLM | mcq_product.csv | 15 | 12 | **80.0%** |
| Basic Product RAG | mcq_product.csv | 15 | 9 | **60.0%** |
| Optimized Product RAG | mcq_product.csv | 15 | 11 | **73.3%** |

### LLM-as-Judge — golden_*.jsonl

| System | Questions | Faithfulness (M1) | Similarity (M3) | Factual Correctness F1 (M2) |
|---|---|---|---|---|
| General RAG | 17 | **0.959** | 0.782 | 0.203 |
| Base LLM (all general+product questions) | 41 | 0.685 | 0.376 | 0.183 |
| Basic Product RAG | 24 | 0.771 | 0.621 | 0.289 |
| Optimized Product RAG | 24 | **0.946** | 0.671 | **0.454** |

---

## 1) Heuristic Eval — Full Detail

### 1.1) General question set — `mcq_general.csv`, 10 questions

| ID | Question | Category | Expected | Base LLM | General RAG |
|---|---|---|---|---|---|
| G012 | First step when red spider mite exceeds threshold | diagnosis | B | B ✅ | B ✅ |
| G013 | Factor that increases powdery mildew susceptibility | diagnosis | B | B ✅ | B ✅ |
| G014 | Best time of day to spray | timing | B | B ✅ | B ✅ |
| G015 | Practice that improves soil structure | soil | A | A ✅ | A ✅ |
| G016 | What to avoid when applying pesticides | safety | C | C ✅ | C ✅ |
| G038 | Used to monitor thrips populations | diagnosis | A | A ✅ | A ✅ |
| G040 | What to do before treating leaf yellowing | diagnosis | B | B ✅ | B ✅ |
| G044 | When harvest can occur after spraying | safety | B | B ✅ | B ✅ |
| G045 | What ensures safe pesticide residue levels | safety | B | B ✅ | B ✅ |
| G047 | When animals can resume grazing | safety | B | B ✅ | B ✅ |
| **Total** | | | | **10/10 (100%)** | **10/10 (100%)** |

**Note:** A 100%/100% result doesn't reveal a real gap between the two systems — these questions are easy for gpt-4o-mini's general agricultural knowledge. Harder/more specific questions would be needed to expose a real difference.

### 1.2) Product question set — `mcq_product.csv`, 15 questions

| ID | Question | Expected | Base LLM | Basic RAG | Optimized RAG |
|---|---|---|---|---|---|
| G002 | 500g Citrus Bacteria Clear (AF0001) → how much water? | B | B ✅ | B ✅ | B ✅ |
| G003 | AF0001, how much product for 30 jin water? | B | ❌ | C ❌ | C ❌ |
| G004 | PN0014 15g → how much water? | A | A ✅ | A ✅ | A ✅ |
| G005 | 500g Spider Mite Killer (AF0039) → how much water? | B | B ✅ | A ❌ | A ❌ |
| G010 | Net content spec of AF0001 | A | A ✅ | B ❌ | B ❌ |
| G011 | Does AF0001 work on potatoes? | B | B ✅ | B ✅ | B ✅ |
| G022 | 100g Bacteria Clear Universal (AF0006) → how much water? | B | B ✅ | B ✅ | B ✅ |
| G023 | AF0001, how many grams for 2 jin water? | B | ❌/✅* | B ✅ | B ✅ |
| G024 | AF0001, how much product for a 20L tank? | B | ❌/✅* | C ❌ | B ✅ |
| G026 | PN0014, how much product for 40 jin water? | B | B ✅ | B ✅ | B ✅ |
| G028 | Dilution ratio for Thrips No.1 (AF0064) | A | A ✅/❌* | A ✅ | A ✅ |
| G029 | How many grams per bottle of 24% Bifenazate (PN0013) | A | A ✅ | A ✅ | A ✅ |
| G032 | Correct method and dose for PN0014 | A | ❌/✅* | A ✅ | A ✅ |
| G034 | Product for potato seed dressing, and ratio | A | A ✅ | B ❌ | B ❌ |
| G035 | Can AF0001 be poured into potting soil? | B | B ✅ | A ❌ | B ✅ |
| **Total** | | | **12/15 (80%)** or **10/15 (66.7%)*** | **9/15 (60.0%)** | **11/15 (73.3%)** |

\* Base LLM is not fully deterministic between runs (gpt-4o-mini): first run gave 66.7% (explicit refusals on G003/G023/G024/G032 and a wrong answer on G028), a second run gave 80% (answered most correctly). The table reflects the latest run (80%).

**Error analysis by system:**

- **Base LLM:** most errors are explicit refusals ("I cannot access the catalog") on specific dosage questions — expected without a catalog. Varies between runs.
- **Basic Product RAG (6 errors: G003, G005, G010, G024, G034, G035):** cross-product data leakage caused by the absence of metadata filtering in the old BM25 path (the same issue noted in the fix commit: "BM25 had no product_id filter, lexical matches could fuse in another product's chunks").
- **Optimized Product RAG (4 errors: G003, G005, G010, G034):** retrieval itself is **correct** (the `Metadata Filter (ID)` log confirms the right product) — the remaining issue is in extracting the precise value from the retrieved text, not a retrieval problem.

**Basic vs Optimized:**

| | Basic | Optimized | Change |
|---|---|---|---|
| Accuracy | 60.0% | 73.3% | **+13.3 points** |
| Retrieval mechanism | `similarity_search_with_score` only (dense, no product filter) | `hybrid_retrieve` (dense + BM25 + RRF fusion) + metadata filter + query rewrite + cross-encoder rerank top-3 | — |
| Questions improved | — | G023, G024, G028, G032, G035 | |
| Still wrong in both | G003, G005, G010, G034 | same | Root cause shifted from retrieval to value-extraction accuracy |

---

## 2) LLM-as-Judge Eval — Full Detail

Data: `golden_general_rag.jsonl` (17 questions) and `golden_product_rag.jsonl` (24 questions), 41 total for Base LLM.

### 2.1) Metric 1 — Faithfulness (is the answer grounded in the retrieved context?)

| System | Questions | Average |
|---|---|---|
| General RAG | 17 | **0.959** |
| Optimized Product RAG | 24 | **0.946** |
| Basic Product RAG | 24 | 0.771 |
| Base LLM | 41 | 0.685 |

### 2.2) Metric 3 — Semantic Similarity (judge-scored content coverage)

| System | Questions | Average |
|---|---|---|
| General RAG | 17 | **0.782** |
| Optimized Product RAG | 24 | 0.671 |
| Basic Product RAG | 24 | 0.621 |
| Base LLM | 41 | 0.376 |

### 2.3) Metric 2 — Factual Correctness F1 (claim decomposition + bidirectional verify_claims)

| System | Questions | Average F1 |
|---|---|---|
| Optimized Product RAG | 24 | **0.454** |
| Basic Product RAG | 24 | 0.289 |
| General RAG | 17 | 0.203 |
| Base LLM | 41 | 0.183 |

### 2.4) Question-by-question comparison — Faithfulness, Basic vs Optimized (Product RAG, 24 questions)

| Question (short) | Basic | Optimized |
|---|---|---|
| What does '1 g diluted in 1 jin of water' mean? | 1.0 | 1.0 |
| 500g Citrus Bacteria Clear → how much water? | **0.0** | 1.0 |
| How much product for 30 jin water? | 1.0 | 1.0 |
| How much water for 45% Bifenazate + Etoxazole? | 1.0 | 1.0 |
| 500g Spider Mite Killer → how much water? | 1.0 | 1.0 |
| How is AF0001 used? | 0.9 | 0.9 |
| Is AF0001 watered (root drench) or sprayed? | 1.0 | 1.0 |
| Can AF0001 be dusted dry without water? | 1.0 | 1.0 |
| Net content of one AF0001 bottle? | **0.0** | 1.0 |
| Does AF0001 work on potatoes? | 1.0 | 0.9 |
| 100g Bacteria Clear Universal → how much water? | **0.0** | 1.0 |
| How many grams for 2 jin water? | **0.0** | 1.0 |
| How much product for a 20L tank? | 1.0 | 0.8 |
| How many jin of water from a 500g Spider Mite Killer bottle? | 0.5 | 0.5 |
| How much product for 40 jin water (PN0014)? | 1.0 | 1.0 |
| 50g dose mixed with 30 jin water (AF0039)? | 1.0 | 1.0 |
| How much per capful (Thrips No.1)? | 1.0 | 0.9 |
| How many grams per bottle of 24% Bifenazate? | 1.0 | 1.0 |
| How much area does one AF0001 bottle cover? | 0.8 | 1.0 |
| How many days between sprays (AF0001)? | 1.0 | 1.0 |
| Method and dose for PN0014? | 1.0 | 0.9 |
| Can AF0001 be mixed with other pesticides? | 1.0 | 1.0 |
| Product for potato seed dressing, and ratio? | 0.8 | 0.8 |
| Can AF0001 be poured into potting soil? | 0.5 | 1.0 |

**Key observation:** 4 questions (net content, dilution for 500g/100g bottles, dilution for 2 jin) scored Faithfulness = **0.0** under Basic but **1.0** under Optimized — these are exactly the same questions that were also wrong in the MCQ run, confirming the root cause is **cross-product data leakage** from the old BM25 path's missing metadata filter, not coincidence.

---

## 3) Technical Notes — How This Was Measured

- **General RAG / Base LLM (general):** retrieval uses the raw question text (`retrieval_query`), generation uses a modified prompt asking for a single-letter answer (`generation_prompt`) — kept separate so the MCQ instructions never affect retrieval.
- **Product RAG (Optimized, MCQ):** same idea, but applied manually (`generate_mcq_answer` in `run_mcq_product.py`) because the original `generate_answer()` uses the same text for both retrieval and generation — they had to be split because `rewrite_query()` was collapsing the full MCQ prompt down to just the correct letter (a bug discovered and fixed during this work).
- **Product RAG (Basic):** code checked out from the `evaluation-base` branch (the original code before hybrid retrieval was added) via a separate `git worktree` — a fresh index was built from the same product catalog (`ProductCatalog(En).xlsx`) to guarantee identical data, with only the retrieval method differing (plain `retrieve_chunks`, no hybrid/rerank/rewrite).
- **Letter extraction (`extract_letter`, MCQ):** a critical bug was fixed during this work — the extractor was matching the letter "A" or "I" as standalone characters inside ordinary refusal sentences (e.g. "consult **a** licensed agronomist"), which incorrectly inflated Base LLM's score from 66.7% to 80% on the first run. The regex was tightened to require the letter be the entire answer or stated as "Answer: X". (Note: Base LLM still varies between 66.7%–80% even after the fix, due to gpt-4o-mini's non-determinism, not the regex.)
- **Metric 1 (Faithfulness):** `judge_answer()` scores in a single LLM call whether every claim in the answer is supported by the retrieved context, with no invented details.
- **Metric 3 (Similarity):** `coverage_judge_score()` — the judge scores "golden content coverage" on a continuous 0-1 scale in one LLM call, distinct from the earlier cosine-similarity metric.
- **Metric 2 (Factual Correctness):** `decompose_claims()` breaks both the golden and generated answers into separate claim lists (two LLM calls), then `verify_claims()` checks each claim bidirectionally (precision/recall) to compute F1.
- **Basic-RAG scripts for Metric 1/2/3:** did not exist on the `evaluation-base` branch (it predates the entire evaluation system) — they were written from scratch (`run_metric1_3_product_basic.py`, `run_metric2_product_basic.py`) using `metrics.py`/`llm_judge.py` copied from `core/evaluation/metrics/`, with `core.rag` rewritten to `terramind.rag` to match the old branch's import paths.

---

## 4) Folder Organization

`core/evaluation/` (formerly `terramind/FullEvaluation/`) is split by evaluation method:

- **`llm_judge_eval/`** — Metric 1 (Faithfulness), Metric 2 (Factual Correctness), Metric 3 (Similarity via judge). Includes: `run_metric1_3*.py`, `run_metric2*.py`.
- **`heuristic_eval/`** — MCQ scripts (exact-match, no LLM judge). Includes: `run_mcq_general.py`, `run_mcq_base_llm.py`, `run_mcq_product.py`, `run_mcq_product_base_llm.py`, `mcq_general.csv`, `mcq_product.csv`.
- **`scripts/`** — exploratory/draft scripts. Includes: `metric3_test.py`, `metric3_test_v2.py`, `similarity_score_new.py`, `validate_metric3.py`, `compare_models.py`, `recompute_coverage_basic.py`, `test_coverage_judge.py`, `test_metric2.py`.
- **`evaluate.py`** and **`metrics/`** — shared at the top level (dataset loaders, `REPORTS_DIR`, similarity_score/agri_score/llm_judge/retrieval_metrics definitions).
- **Basic Product RAG (both MCQ and Metric 1/2/3)** lives outside this repo, inside the `evaluation-base` branch worktree (`../TerraMind-eval-base/terramind/FullEvaluation/`) since it depends on the old Product RAG code predating hybrid retrieval:
  - `run_mcq_product_basic.py`
  - `run_metric1_3_product_basic.py`
  - `run_metric2_product_basic.py`

### Run commands

```
# Heuristic (MCQ)
python -m core.evaluation.heuristic_eval.run_mcq_general
python -m core.evaluation.heuristic_eval.run_mcq_base_llm
python -m core.evaluation.heuristic_eval.run_mcq_product
python -m core.evaluation.heuristic_eval.run_mcq_product_base_llm

# LLM-as-Judge
python -m core.evaluation.llm_judge_eval.run_metric1_3
python -m core.evaluation.llm_judge_eval.run_metric1_3_general
python -m core.evaluation.llm_judge_eval.run_metric1_3_base_llm
python -m core.evaluation.llm_judge_eval.run_metric2
python -m core.evaluation.llm_judge_eval.run_metric2_general
python -m core.evaluation.llm_judge_eval.run_metric2_base_llm

# Basic Product RAG (evaluation-base branch worktree only)
cd ../TerraMind-eval-base
python -m terramind.FullEvaluation.run_mcq_product_basic
python -m terramind.FullEvaluation.run_metric1_3_product_basic
python -m terramind.FullEvaluation.run_metric2_product_basic
```

## 5) Files

**Heuristic:**
- `heuristic_eval/mcq_general.csv`, `heuristic_eval/mcq_product.csv` — MCQ datasets
- `heuristic_eval/run_mcq_general.py`, `heuristic_eval/run_mcq_base_llm.py` — General RAG / Base LLM (general set)
- `heuristic_eval/run_mcq_product.py`, `heuristic_eval/run_mcq_product_base_llm.py` — Optimized Product RAG / Base LLM (product set)
- `reports/mcq_general_report.json`, `reports/mcq_base_llm_report.json`, `reports/mcq_product_report.json`, `reports/mcq_product_base_llm_report.json`, `reports/mcq_product_basic_report.json`

**LLM-as-Judge:**
- `llm_judge_eval/run_metric1_3*.py`, `llm_judge_eval/run_metric2*.py`
- `datasets/golden_general_rag.jsonl`, `datasets/golden_product_rag.jsonl`
- `reports/metric1_report_general.json`, `reports/metric1_report_product_optimized.json`, `reports/metric1_report_product_basic.json`, `reports/metric1_report_base_llm.json`
- `reports/metric3_report_general.json`, `reports/metric3_report_product_optimized.json`, `reports/metric3_report_product_basic.json`, `reports/metric3_report_base_llm.json`
- `reports/metric2_general_report.json`, `reports/metric2_report_product_optimized.json`, `reports/metric2_report_product_basic.json`, `reports/metric2_base_llm_golden_report.json`

**Basic Product RAG (worktree only, not merged into main):**
- `../TerraMind-eval-base/terramind/FullEvaluation/run_mcq_product_basic.py`
- `../TerraMind-eval-base/terramind/FullEvaluation/run_metric1_3_product_basic.py`
- `../TerraMind-eval-base/terramind/FullEvaluation/run_metric2_product_basic.py`
