/** Match core/rag/scoring.py confidence bands. */
export const CONFIDENCE_HIGH = 0.52;
export const CONFIDENCE_MEDIUM = 0.38;

export function formatConfidence(level) {
  if (!level) return "—";
  const s = String(level).toLowerCase();
  return s.charAt(0).toUpperCase() + s.slice(1);
}

export function formatRetrievalPct(score) {
  if (score == null || Number.isNaN(Number(score))) return null;
  return `${Math.round(Number(score) * 100)}%`;
}

export function relevanceLabel(score) {
  if (score == null || Number.isNaN(Number(score))) return null;
  const n = Number(score);
  if (n >= CONFIDENCE_HIGH) return "Strong";
  if (n >= CONFIDENCE_MEDIUM) return "Good";
  return "Weak";
}

export function confidencePhrase(level, ar = false) {
  const s = String(level || "").toLowerCase();
  if (ar) {
    if (s === "high") return "تطابق قوي مع سؤالك";
    if (s === "medium") return "تطابق جزئي — تحقق محلياً";
    if (s === "low") return "تطابق ضعيف — تحقق محلياً";
    return "—";
  }
  if (s === "high") return "Strong match to your question";
  if (s === "medium") return "Partial match — verify locally";
  if (s === "low") return "Weak match — verify locally";
  return "—";
}

export function confidenceDotColor(level, t) {
  const s = String(level || "").toLowerCase();
  if (s === "high") return t.accent;
  if (s === "medium") return t.accentWheat || "#c4a35a";
  return t.text4;
}

/** Show confidence only when vector retrieval actually ran. */
export function shouldShowRetrievalConfidence({
  routedTo,
  modelId,
  retrievedChunks,
  retrievalScore,
  confidence,
}) {
  if (!confidence || String(confidence).trim() === "") return false;
  const backend = routedTo || modelId;
  if (backend === "base_llm") return false;
  if (
    modelId === "advisory" &&
    (retrievedChunks ?? 0) === 0 &&
    retrievalScore == null
  ) {
    return false;
  }
  if ((retrievedChunks ?? 0) > 0) return true;
  return retrievalScore != null && !Number.isNaN(Number(retrievalScore));
}

export function sourceKind(src) {
  const s = (src?.source || "").toLowerCase();
  if (s === "product_catalog" || s.includes("product")) return "product";
  return "general";
}
