"""
تجربة صغيرة: مقارنة ٣ طرق لحساب متركس ٣
- الحالية: MiniLM + نص كامل
- مُحسّنة: mpnet + نص كامل
- claim-level: تفكيك + مطابقة معنى (max-align)

التشغيل:  pip install sentence-transformers
          python metric3_test.py
"""
import numpy as np
from sentence_transformers import SentenceTransformer
import re

# ---------- بيانات الاختبار ----------
# G014: تباعد محتوى حقيقي (golden=حرارة/تبخر، generated=ملقحات/طقس)
# G045: محتوى صح، طويل فقط (نبي نرفعه)

cases = {
    "G014": {
        "golden": "Spraying before 10 AM or after 4 PM avoids peak heat. High heat increases spray evaporation. High heat increases the risk of leaf burn. Cooler conditions improve pesticide uptake by the plant.",
        "generated": "## Best Time to Spray\n\nThe timing of pesticide application matters significantly. Spray in the early evening or at night to protect bees and pollinators, which are most active during the day. Avoid spraying when winds exceed 10 km/h to prevent drift onto neighboring areas. Do not spray before expected rainfall, as this washes away the product and reduces efficacy. Check the weather forecast and choose calm, dry conditions for best results.",
        "old_metric3": 0.62,
    },
    "G045": {
        "golden": "Vegetables should only be eaten after the pre-harvest interval has passed. Produce should be washed before eating. The interval ensures residues are within safe limits.",
        "generated": "## Is It Safe to Eat Vegetables After Spraying?\n\n### 1. Pre-Harvest Interval (PHI)\nEvery pesticide has a pre-harvest interval, the minimum time that must pass between the last spray and harvest. Do not harvest or eat produce before this interval ends.\n\n### 2. Washing Produce\nWashing fruits and vegetables thoroughly under running water helps remove any pesticide residues remaining on the surface.\n\n### 3. Safe Residue Limits\nThe pre-harvest interval is set so that residues decline to levels considered safe for consumption.\n\n### 4. Good Hygiene\nAlways clean equipment and practice personal hygiene when handling treated produce.",
        "old_metric3": 0.55,
    },
}

# ---------- تفكيك بسيط لادعاءات ----------
def split_claims(text):
    # نشيل عناوين Markdown والترقيم
    text = re.sub(r'#+\s*', '', text)
    text = re.sub(r'^\s*\d+\.\s*', '', text, flags=re.MULTILINE)
    # نقسم على الجمل
    parts = re.split(r'(?<=[.!?])\s+|\n+', text)
    claims = [p.strip() for p in parts if len(p.strip()) > 15]
    return claims

# ---------- الطرق الثلاث ----------
def cosine(a, b):
    return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b)))

def fulltext_sim(model, golden, generated):
    e = model.encode([golden, generated])
    return cosine(e[0], e[1])

def claim_level_sim(model, golden, generated):
    gc = split_claims(golden)
    pc = split_claims(generated)
    if not gc or not pc:
        return 0.0
    ge = model.encode(gc)
    pe = model.encode(pc)
    # لكل ادعاء ذهبي: أقصى تشابه مع أقرب ادعاء مولّد
    sims = []
    for g in ge:
        best = max(cosine(g, p) for p in pe)
        sims.append(best)
    return float(np.mean(sims))

# ---------- تشغيل ----------
print("جاري تحميل النماذج...")
mini = SentenceTransformer('all-MiniLM-L6-v2')
mpnet = SentenceTransformer('all-mpnet-base-v2')

print("\n" + "="*70)
for qid, d in cases.items():
    print(f"\n[{qid}]")
    print(f"  الحالي (MiniLM + نص كامل، من التقرير): {d['old_metric3']:.3f}")
    m1 = fulltext_sim(mini, d['golden'], d['generated'])
    print(f"  (تحقّق) MiniLM + نص كامل:              {m1:.3f}")
    m2 = fulltext_sim(mpnet, d['golden'], d['generated'])
    print(f"  mpnet + نص كامل:                        {m2:.3f}")
    m3 = claim_level_sim(mpnet, d['golden'], d['generated'])
    print(f"  mpnet + claim-level (max-align):        {m3:.3f}")
print("\n" + "="*70)
