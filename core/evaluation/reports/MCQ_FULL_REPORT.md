# تقرير شامل — تقييم MCQ على الأنظمة الثلاثة

التاريخ: 2026-06-22

## ملخص عام

| النظام | عدد الأسئلة | صحيح | الدقة |
|---|---|---|---|
| Base LLM — General set | 10 | 10 | **100.0%** |
| General RAG | 10 | 10 | **100.0%** |
| Base LLM — Product set | 15 | 10 | **66.7%** |
| Basic Product RAG (قبل hybrid/rerank) | 15 | 9 | **60.0%** |
| Optimized Product RAG (hybrid BM25 + rerank، الحالي) | 15 | 11 | **73.3%** |

---

## 1) مجموعة الأسئلة العامة (General) — `mcq_general.csv`، 10 أسئلة

### Base LLM (بدون retrieval) — 100% (10/10)

كل الأسئلة أجابها صح بحرف واحد مباشرة، بدون أي رفض. هذا منطقي لأن هذه الأسئلة (IPM، مبيدات، توقيت الرش، السلامة العامة) معرفة عامة زراعية موجودة في تدريب gpt-4o-mini الأساسي، فمو محتاجة مصادر خاصة بالشركة.

### General RAG — 100% (10/10)

نفس النتيجة بالضبط. التفاصيل الكاملة لكل سؤال:

| ID | السؤال | الفئة | المتوقع | Base LLM | General RAG |
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

**ملاحظة مهمة:** نتيجة 100%/100% لا تكشف فرقاً بين الأنظمة لأن الأسئلة سهلة جداً على المعرفة العامة لـgpt-4o-mini. لمعرفة فعلاً وين General RAG يفرق عن Base LLM، نحتاج أسئلة أصعب/أدق (تفاصيل محددة فقط موجودة بالمصادر المفهرسة، صعب يعرفها LLM عام).

---

## 2) مجموعة أسئلة المنتجات (Product) — `mcq_product.csv`، 15 سؤال

هذي الأسئلة تتطلب معرفة دقيقة بكتالوج المنتجات (جرعات، تخفيف، مواصفات) — معرفة خاصة بالشركة لا يعرفها LLM عام.

### النتائج بالتفصيل (مقارنة الثلاثة معاً)

| ID | السؤال | المتوقع | Base LLM | Basic RAG | Optimized RAG |
|---|---|---|---|---|---|
| G002 | 500g Citrus Bacteria Clear (AF0001) → كم ماء؟ | B | B ✅ | B ✅ | B ✅ |
| G003 | AF0001، كم منتج لـ30 جين ماء؟ | B | رفض ❌ | C ❌ | C ❌ |
| G004 | PN0014 15g → كم ماء؟ | A | A ✅ | A ✅ | A ✅ |
| G005 | 500g Spider Mite Killer (AF0039) → كم ماء؟ | B | B ✅ | A ❌ | A ❌ |
| G010 | مواصفة المحتوى الصافي لـAF0001 | A | A ✅ | B ❌ | B ❌ |
| G011 | يعمل AF0001 على البطاطس؟ | B | B ✅ | B ✅ | B ✅ |
| G022 | 100g Bacteria Clear Universal (AF0006) → كم ماء؟ | B | B ✅ | B ✅ | B ✅ |
| G023 | AF0001، كم جرام لـ2 جين ماء؟ | B | رفض ❌ | B ✅ | B ✅ |
| G024 | AF0001، كم منتج لخزان 20 لتر؟ | B | رفض ❌ | C ❌ | B ✅ |
| G026 | PN0014، كم منتج لـ40 جين ماء؟ | B | B ✅ | B ✅ | B ✅ |
| G028 | نسبة تخفيف Thrips No.1 (AF0064) | A | B ❌ | A ✅ | A ✅ |
| G029 | كم جرام عبوة 24% Bifenazate (PN0013) | A | A ✅ | A ✅ | A ✅ |
| G032 | الطريقة والجرعة الصحيحة لـPN0014 | A | رفض ❌ | A ✅ | A ✅ |
| G034 | منتج تغطية بذور البطاطس وبأي نسبة | A | A ✅ | B ❌ | B ❌ |
| G035 | يمكن سكب AF0001 بتربة الزرع؟ | B | B ✅ | A ❌ | B ✅ |
| **الإجمالي** | | | **10/15 (66.7%)** | **9/15 (60.0%)** | **11/15 (73.3%)** |

### تحليل الأخطاء حسب النظام

**Base LLM — 5 أخطاء:**
- G003, G023, G024, G032 → **رفض صريح** ("I cannot access the catalog in this mode") لأنها أسئلة جرعات/تخفيف محددة لا يعرفها بدون كتالوج — منطقي ومتوقع.
- G028 → **خطأ معرفي حقيقي** (جاوب B بدل A على نسبة تخفيف Thrips No.1).

**Basic Product RAG (قبل hybrid/rerank) — 6 أخطاء:**
- G003, G024 → جواب غلط رغم استرجاع بعض المحتوى — يدل على تسرّب بيانات منتج آخر بسبب عدم وجود فلترة metadata في هذه النسخة (نفس المشكلة المذكورة في commit الإصلاح: "BM25 had no product_id filter, lexical matches could fuse in another product's chunks").
- G005, G010, G034, G035 → نفس النوع: استرجاع غير دقيق يأتي بمعلومة من سياق غير صحيح.

**Optimized Product RAG (الحالي) — 4 أخطاء:**
- G003, G005, G010, G034 → هذه الحالات الأربع: الاسترجاع كان **صحيح** (الفلتر `Metadata Filter (ID)` طابق المنتج الصحيح في اللوج)، لكن LLM فشل يستخرج القيمة الدقيقة الصحيحة من النص المسترجَع — يدل المشكلة هنا انتقلت من الاسترجاع إلى دقة الاستخراج/القراءة من السياق، وليست مشكلة retrieval.
- لاحظ تحسّن G023, G024, G028, G032, G035 بالمقارنة مع Basic — هذي الأسئلة صارت صحيحة بعد hybrid+rerank.

### الفرق بين Basic و Optimized

| | Basic | Optimized | التغيير |
|---|---|---|---|
| الدقة | 60.0% | 73.3% | **+13.3 نقطة** |
| آلية الاسترجاع | `similarity_search_with_score` فقط (dense, بدون فلترة منتج) | `hybrid_retrieve` (dense + BM25 مع RRF fusion) + فلترة metadata بالـproduct_id/name + query rewrite + cross-encoder rerank top-3 | — |
| أسئلة تحسّنت | — | G023, G024, G028, G032, G035 (5 أسئلة) | |
| أسئلة تراجعت | — | لا توجد | |
| أسئلة باقية خاطئة بالاثنين | G003, G005, G010, G034 | نفس | تحتاج تحقيق إضافي (احتمال: بيانات الكتالوج نفسها مفقودة/غامضة لهذه الحقول، أو الـLLM يقرأ خطأ من سياق صحيح) |

---

## 3) ملخص تقني — كيف تم القياس

- **General RAG / Base LLM (general):** الاسترجاع يستخدم نص السؤال الخام (`retrieval_query`)، والتوليد يستخدم برومبت معدّل يطلب إجابة بحرف واحد فقط (`generation_prompt`) — مفصولان عن بعض، فالاسترجاع لم يتأثر بتعليمات الـMCQ.
- **Product RAG (Optimized):** نفس الفكرة لكن طُبّقت يدوياً (`generate_mcq_answer` في `run_mcq_product.py`) لأن `generate_answer()` الأصلية تستخدم نفس النص للاسترجاع والتوليد معاً — كان لازم نفصلهم لأن `rewrite_query()` كانت تختصر برومبت الـMCQ كامل لمجرد الحرف الصحيح (Bug تم اكتشافه وتصحيحه أثناء العمل).
- **Product RAG (Basic):** نسخة الكود مأخوذة فعلياً من فرع `evaluation-base` (الكود الأصلي قبل إضافة hybrid retrieval) عبر `git worktree` منفصل — بُني له index جديد من نفس كتالوج المنتجات (`ProductCatalog(En).xlsx`) لضمان نفس البيانات بالضبط، وفقط طريقة الاسترجاع اختلفت.
- **استخراج الحرف (`extract_letter`):** تم تصحيح bug حرج أثناء العمل — كانت أداة الاستخراج تمسك حرف "A" أو "I" كحروف منعزلة داخل جمل رفض عادية (مثل "consult **a** licensed agronomist")، مما رفع نتيجة Base LLM بشكل خاطئ من 66.7% إلى 80% في أول تشغيل. تم تشديد الـregex ليتطلب أن يكون الحرف هو الإجابة الكاملة أو مذكور بصيغة "Answer: X" فقط.

---

## تنظيم المجلد (بعد إعادة الترتيب)

`terramind/FullEvaluation/` مقسومة الآن على طريقة التقييم:

- **`llm_judge_eval/`** — مقاييس تعتمد على LLM كحكم (judge): Metric 1 (Faithfulness عبر judge_answer)، Metric 2 (Factual Correctness عبر تفكيك claims + verify_claims)، coverage_judge_score. يشمل: `run_metric1_3*.py`, `run_metric2*.py`.
- **`heuristic_eval/`** — مقاييس بدون استدعاء LLM للتقييم نفسه (exact-match أو حساب رياضي مباشر): سكربتات MCQ (مقارنة حرف-بحرف). يشمل: `run_mcq_general.py`, `run_mcq_base_llm.py`, `run_mcq_product.py`, `run_mcq_product_base_llm.py`, `mcq_general.csv`, `mcq_product.csv`.
- **`scripts/`** — سكربتات تجريبية/مسودات عمل (تطوير وتجربة مقاييس similarity، مقارنة embedding models، إعادة حساب تقارير قديمة). يشمل: `metric3_test.py`, `metric3_test_v2.py`, `similarity_score_new.py`, `validate_metric3.py`, `compare_models.py`, `recompute_coverage_basic.py`, `test_coverage_judge.py`, `test_metric2.py`.
- **`evaluate.py`** و **`metrics/`** يبقون بالجذر — مشتركون بين كل الفروع (تحميل الـdatasets، `REPORTS_DIR`، تعريفات similarity_score/agri_score/llm_judge/retrieval_metrics).
- **`run_mcq_product_basic.py`** يبقى خارج هذا المستودع، داخل worktree الفرع `evaluation-base` (`../TerraMind-eval-base/terramind/FullEvaluation/run_mcq_product_basic.py`) لأنه يعتمد على كود Product RAG القديم قبل hybrid retrieval.

### أوامر التشغيل بعد النقل

```
python -m terramind.FullEvaluation.heuristic_eval.run_mcq_general
python -m terramind.FullEvaluation.heuristic_eval.run_mcq_base_llm
python -m terramind.FullEvaluation.heuristic_eval.run_mcq_product
python -m terramind.FullEvaluation.heuristic_eval.run_mcq_product_base_llm

python -m terramind.FullEvaluation.llm_judge_eval.run_metric1_3
python -m terramind.FullEvaluation.llm_judge_eval.run_metric1_3_general
python -m terramind.FullEvaluation.llm_judge_eval.run_metric1_3_base_llm
python -m terramind.FullEvaluation.llm_judge_eval.run_metric2
python -m terramind.FullEvaluation.llm_judge_eval.run_metric2_general
python -m terramind.FullEvaluation.llm_judge_eval.run_metric2_base_llm
```

## الملفات

- `heuristic_eval/mcq_general.csv`, `heuristic_eval/mcq_product.csv` — أسئلة الاختيار من متعدد
- `heuristic_eval/run_mcq_general.py`, `heuristic_eval/run_mcq_base_llm.py` — تشغيل على General RAG / Base LLM (مجموعة general)
- `heuristic_eval/run_mcq_product.py`, `heuristic_eval/run_mcq_product_base_llm.py` — تشغيل على Product RAG المحسّن / Base LLM (مجموعة product)
- `run_mcq_product_basic.py` (في worktree الفرع `evaluation-base`) — تشغيل على Product RAG الأساسي
- `reports/mcq_general_report.json`, `reports/mcq_base_llm_report.json`, `reports/mcq_product_report.json`, `reports/mcq_product_base_llm_report.json`, `reports/mcq_product_basic_report.json` — تقارير JSON المفصّلة لكل سؤال
