"""
Compare embedding models for Metric 3
=====================================
Tries several models on your existing data (full text, same method as
the current code) and prints a table: which model improves the scores
the most.

Run:
    pip install sentence-transformers
    python compare_models.py core/evaluation/.../metric3_report_general.json

Accepts multiple files:
    python compare_models.py general.json product.json base.json
"""
import sys, json
import numpy as np
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity

# Candidate models (lightest to heaviest)
MODELS = [
    "all-MiniLM-L6-v2",            # current — for comparison
    "all-mpnet-base-v2",
    "BAAI/bge-base-en-v1.5",
]

# Some models need a prefix (bge/e5) — add it automatically
def encode(model, name, texts):
    if "bge" in name:
        texts = [f"Represent this sentence: {t}" for t in texts]
    elif "e5" in name:
        texts = [f"query: {t}" for t in texts]
    return model.encode(texts)

def score(model, name, g, p):
    e = encode(model, name, [g, p])
    return float(cosine_similarity([e[0]], [e[1]])[0][0])

# Collect all questions from all files
items = []
for path in sys.argv[1:] or ["metric3_report_general.json"]:
    data = json.load(open(path, encoding="utf-8"))
    for r in data["results"]:
        items.append({"id": r.get("id", r["question"][:20]), "g": r["golden"],
                      "p": r["generated"], "old": r.get("similarity")})

print(f"\nNumber of questions: {len(items)}\n")
print("Running... (first-time model download may take a while)\n")

# Compute scores for each model
cols = {}
for name in MODELS:
    print(f"  -> {name}")
    m = SentenceTransformer(name)
    cols[name] = [score(m, name, it["g"], it["p"]) for it in items]
    del m

# Summary table
print("\n" + "="*70)
print(f"{'Model':<28}{'Mean':>8}{'>=0.7':>9}{'<0.5':>9}")
print("-"*70)
for name in MODELS:
    v = np.array(cols[name])
    print(f"{name:<28}{v.mean():>8.3f}{sum(v>=0.7):>6}/{len(v)}{sum(v<0.5):>6}/{len(v)}")
print("="*70)

# Per-question breakdown (optional — saved to file)
out = []
for i, it in enumerate(items):
    row = {"id": it["id"], "old": it["old"]}
    for name in MODELS:
        row[name.split("/")[-1]] = round(cols[name][i], 3)
    out.append(row)
json.dump(out, open("model_comparison.json", "w", encoding="utf-8"),
          ensure_ascii=False, indent=2)
print("\nFull breakdown saved to: model_comparison.json")
print("Check the table above and pick the model with the highest mean and most scores >= 0.7")
