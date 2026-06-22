"""
Validation script: compares the old metric against the new one on the
same data. Run it on metric3_report_general.json (or any report)
before adopting the change.

Run:
    python validate_metric3.py path/to/metric3_report_general.json
"""
import sys, json
import numpy as np
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
import re

model = SentenceTransformer("all-MiniLM-L6-v2")

def _split(text):
    text = re.sub(r'#+\s*', ' ', text)
    text = re.sub(r'\*\*', '', text)
    text = re.sub(r'^\s*\d+\.\s*', ' ', text, flags=re.M)
    text = re.sub(r'^\s*[-•]\s*', ' ', text, flags=re.M)
    parts = re.split(r'(?<=[.!?])\s+|\n+', text)
    return [p.strip() for p in parts if len(p.strip()) > 12]

def old_score(g, p):
    e1, e2 = model.encode(g), model.encode(p)
    return float(cosine_similarity([e1],[e2])[0][0])

def new_score(g, p):
    gc, pc = _split(g), _split(p)
    if not gc or not pc:
        return old_score(g, p)
    sim = cosine_similarity(model.encode(gc), model.encode(pc))
    return float(sim.max(axis=1).mean())

path = sys.argv[1] if len(sys.argv) > 1 else "metric3_report_general.json"
data = json.load(open(path, encoding="utf-8"))
results = data["results"]

print(f"\n{'ID':<8}{'old':>8}{'new':>8}{'diff':>8}")
print("-"*32)
old_all, new_all = [], []
for r in results:
    o = r.get("similarity", old_score(r["golden"], r["generated"]))
    n = new_score(r["golden"], r["generated"])
    old_all.append(o); new_all.append(n)
    flag = " ↑" if n > o + 0.02 else (" ↓" if n < o - 0.02 else "")
    rid = r.get("id", r.get("question", "")[:6])
    print(f"{rid:<8}{o:>8.3f}{n:>8.3f}{n-o:>8.3f}{flag}")

print("-"*32)
print(f"{'mean':<8}{np.mean(old_all):>8.3f}{np.mean(new_all):>8.3f}{np.mean(new_all)-np.mean(old_all):>8.3f}")
print(f"\n>=0.7:  old={sum(x>=0.7 for x in old_all)}/{len(old_all)}"
      f"   new={sum(x>=0.7 for x in new_all)}/{len(new_all)}")
print(f"<0.7 (new): {[results[i].get('id', i) for i,x in enumerate(new_all) if x<0.7]}")
