"""
مقارنة نماذج embedding لمتركس ٣
=====================================
يجرّب عدة نماذج على نفس بياناتك (نص كامل، نفس طريقة الكود الحالي)
ويطلع جدول: أي نموذج يرفع الأرقام بأفضل شكل.

التشغيل:
    pip install sentence-transformers
    python compare_models.py core/evaluation/.../metric3_report_general.json

يقبل عدة ملفات:
    python compare_models.py general.json product.json base.json
"""
import sys, json
import numpy as np
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity

# النماذج المرشّحة (من الأخف للأثقل)
MODELS = [
    "all-MiniLM-L6-v2",            # الحالي — للمقارنة
    "all-mpnet-base-v2",
    "BAAI/bge-base-en-v1.5",
]

# بعض النماذج تحتاج بادئة (bge/e5) — نضيفها تلقائياً
def encode(model, name, texts):
    if "bge" in name:
        texts = [f"Represent this sentence: {t}" for t in texts]
    elif "e5" in name:
        texts = [f"query: {t}" for t in texts]
    return model.encode(texts)

def score(model, name, g, p):
    e = encode(model, name, [g, p])
    return float(cosine_similarity([e[0]], [e[1]])[0][0])

# نجمع كل الأسئلة من كل الملفات
items = []
for path in sys.argv[1:] or ["metric3_report_general.json"]:
    data = json.load(open(path, encoding="utf-8"))
    for r in data["results"]:
        items.append({"id": r.get("id", r["question"][:20]), "g": r["golden"],
                      "p": r["generated"], "old": r.get("similarity")})

print(f"\nعدد الأسئلة: {len(items)}\n")
print("جاري التجربة... (تحميل النماذج قد يأخذ وقت أول مرة)\n")

# نحسب لكل نموذج
cols = {}
for name in MODELS:
    print(f"  -> {name}")
    m = SentenceTransformer(name)
    cols[name] = [score(m, name, it["g"], it["p"]) for it in items]
    del m

# جدول ملخّص
print("\n" + "="*70)
print(f"{'النموذج':<28}{'متوسط':>8}{'فوق0.7':>9}{'تحت0.5':>9}")
print("-"*70)
for name in MODELS:
    v = np.array(cols[name])
    print(f"{name:<28}{v.mean():>8.3f}{sum(v>=0.7):>6}/{len(v)}{sum(v<0.5):>6}/{len(v)}")
print("="*70)

# تفصيل لكل سؤال (اختياري — احفظيه ملف)
out = []
for i, it in enumerate(items):
    row = {"id": it["id"], "old": it["old"]}
    for name in MODELS:
        row[name.split("/")[-1]] = round(cols[name][i], 3)
    out.append(row)
json.dump(out, open("model_comparison.json", "w", encoding="utf-8"),
          ensure_ascii=False, indent=2)
print("\nالتفصيل الكامل محفوظ في: model_comparison.json")
print("شوفي الجدول فوق واختاري النموذج الأعلى متوسطاً والأكثر فوق 0.7")
