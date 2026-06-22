"""
Metric 3 — second experiment with real text
Comparing: current vs claim-level bidirectional

Run: pip install sentence-transformers
     python metric3_test_v2.py
"""
import numpy as np, re
from sentence_transformers import SentenceTransformer

# ---------- real text (matches the report) ----------
cases = {
  "G014": {  # genuinely divergent content -> should stay low
    "golden": "Spraying before 10 AM or after 4 PM avoids peak heat. High heat increases spray evaporation. High heat increases the risk of leaf burn. Cooler conditions improve pesticide uptake by the plant.",
    "generated": "To determine the best time of day for spraying, consider the following guidelines based on your specific crop and disease management needs:\n\n1. Evening or Night Applications: It is advisable to apply fungicides in the evening or at night when temperatures are cooler (less than 13C or 55F). This timing helps reduce the risk of harming beneficial insects, such as pollinators, and can improve the efficacy of the treatment.\n\n2. Avoiding Pollinator Activity: Turn off the sprayer near hives and avoid spraying during the day when pollinators are active. This minimizes exposure to pesticides, which can have lethal and sub-lethal effects on these beneficial insects.\n\n3. Weather Conditions: Ensure that weather conditions are suitable for spraying. Avoid applications during windy conditions or when rain is forecasted shortly after application, as this can wash away the treatment and reduce effectiveness.\n\nSummary of Actions: Spray in the evening or at night when temperatures are cooler. Turn off sprayers near hives to protect pollinators. Monitor weather conditions to ensure effective application.",
    "old": 0.623,
  },
  "G045": {  # correct content, just long -> want it to score higher
    "golden": "Vegetables should only be eaten after the pre-harvest interval has passed. Produce should be washed before eating. The labeled pre-harvest interval ensures residues are within safe limits.",
    "generated": "To determine if it's safe to eat vegetables after spraying, it's essential to consider the following factors:\n\n1. Post-Harvest Intervals (PHIs): These are specific time periods that must pass after pesticide application before crops can be harvested and consumed. Always check the product label for the recommended PHI for the specific pesticide used.\n\n2. Compliance with Application Guidelines: Ensure that you have followed the recommended dosage and application methods as stated on the product label. After applying pesticides, observe personal hygiene practices to prevent any contamination.\n\n3. Pesticide Type: Systemic insecticides can be absorbed by the plant and may remain in edible parts longer than contact insecticides. If a systemic pesticide was used, be particularly cautious about the PHI.\n\n4. Cleaning Produce: Always wash vegetables thoroughly under running water to remove any pesticide residues. This practice can help reduce potential exposure.\n\n5. Consult Local Guidelines: Pesticide regulations can vary by region. Consult local agricultural extension services for specific guidance.\n\nSummary: Check the PHI on the product label. Follow application guidelines strictly. Wash produce thoroughly before consumption. Consult local experts for specific advice.",
    "old": 0.548,
  },
}

def cos(a,b): return float(np.dot(a,b)/(np.linalg.norm(a)*np.linalg.norm(b)))

def claims(t):
    t = re.sub(r'#+\s*','',t)
    t = re.sub(r'^\s*\d+\.\s*','',t,flags=re.M)
    t = re.sub(r'\b(Summary|Summary of Actions)\b:?','',t)
    parts = re.split(r'(?<=[.!?])\s+|\n+', t)
    return [p.strip() for p in parts if len(p.strip())>15]

def fulltext(m,g,p):
    e=m.encode([g,p]); return cos(e[0],e[1])

def claim_recall(m,g,p):
    """For each golden claim: did it find a match? (meaning present)"""
    gc,pc=claims(g),claims(p)
    ge,pe=m.encode(gc),m.encode(pc)
    return np.mean([max(cos(x,y) for y in pe) for x in ge])

def claim_precision(m,g,p):
    """For each generated claim: does it trace back to a golden one? (penalizes extra content)"""
    gc,pc=claims(g),claims(p)
    ge,pe=m.encode(gc),m.encode(pc)
    return np.mean([max(cos(y,x) for x in ge) for y in pe])

def bidir_f1(m,g,p):
    r=claim_recall(m,g,p); pr=claim_precision(m,g,p)
    return 2*r*pr/(r+pr), r, pr

print("Loading MiniLM...")
mini=SentenceTransformer('all-MiniLM-L6-v2')

print("\n"+"="*60)
for qid,d in cases.items():
    print(f"\n[{qid}]  (expected: ",
          "stay low)" if qid=="G014" else "rise above 0.7)")
    print(f"  current (full text):      {d['old']:.3f}")
    f1,r,pr = bidir_f1(mini,d['golden'],d['generated'])
    print(f"  claim recall (meaning):   {r:.3f}")
    print(f"  claim precision (extra):  {pr:.3f}")
    print(f"  claim-F1 (new):           {f1:.3f}")
print("\n"+"="*60)
print("Expectation: G045 rises, G014 stays low, and the gap between them widens")
