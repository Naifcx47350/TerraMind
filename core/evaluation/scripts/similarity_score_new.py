"""
نسخة محسّنة من similarity_score في metrics.py
========================================================
الفكرة: المقياس القديم يقارن النص الكامل بالنص الكامل، فيعاقب
الإجابات الطويلة الصحيحة بسبب الطول. النسخة الجديدة تقيس
"تغطية المحتوى الذهبي" (recall دلالي): لكل جملة من الإجابة
الذهبية موجودة معنى داخل الإجابة المولّدة، الإضافات الزائدة
لا تعاقب بها (نتركها لمتركس 2 المسؤول عنها أصلاً).

التوقيع والمخرجات نفسها تماماً، لا حاجة لتعديل أي runner.
"""
import re
import numpy as np
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity

# نفس النموذج المستخدم حالياً — لا تغيير
model = SentenceTransformer("all-MiniLM-L6-v2")

# زر تحكم: 1.0 = recall فقط (الأعلى للأرقام)
# لو بغيتي صرامة أكثر، نزّليه شوي (مثلاً 0.85) عشان يخلط
# recall مع التشابه الكامل. ابدئي بـ 1.0.
RECALL_WEIGHT = 1.0


def _split_sentences(text: str):
    """تقسيم النص لجمل/ادعاءات قصيرة، مع تنظيف عناوين Markdown والترقيم."""
    text = re.sub(r'#+\s*', ' ', text)            # عناوين ###
    text = re.sub(r'\*\*', '', text)               # **bold**
    text = re.sub(r'^\s*\d+\.\s*', ' ', text, flags=re.M)  # ترقيم 1.
    text = re.sub(r'^\s*[-•]\s*', ' ', text, flags=re.M)   # نقاط
    parts = re.split(r'(?<=[.!?])\s+|\n+', text)
    return [p.strip() for p in parts if len(p.strip()) > 12]


def _recall_coverage(golden: str, generated: str) -> float:
    """
    لكل جملة ذهبية: أقصى تشابه مع أقرب جملة في المولّد.
    المتوسط = نسبة تغطية المحتوى الذهبي.
    """
    g_claims = _split_sentences(golden)
    p_claims = _split_sentences(generated)

    # حالات الحافة: نص قصير لا ينقسم -> رجوع للتشابه الكامل
    if not g_claims or not p_claims:
        e1, e2 = model.encode(golden), model.encode(generated)
        return float(cosine_similarity([e1], [e2])[0][0])

    g_emb = model.encode(g_claims)
    p_emb = model.encode(p_claims)
    sim = cosine_similarity(g_emb, p_emb)   # مصفوفة (ذهبي × مولّد)
    best_per_golden = sim.max(axis=1)        # أقصى تطابق لكل جملة ذهبية
    return float(best_per_golden.mean())


def similarity_score(golden: str, generated: str) -> float:
    """
    بديل متوافق تماماً مع القديم (نفس التوقيع والمخرجات).
    افتراضياً recall فقط. لو RECALL_WEIGHT < 1 يخلط مع التشابه الكامل.
    """
    recall = _recall_coverage(golden, generated)

    if RECALL_WEIGHT >= 1.0:
        return recall

    e1, e2 = model.encode(golden), model.encode(generated)
    full = float(cosine_similarity([e1], [e2])[0][0])
    return RECALL_WEIGHT * recall + (1 - RECALL_WEIGHT) * full
