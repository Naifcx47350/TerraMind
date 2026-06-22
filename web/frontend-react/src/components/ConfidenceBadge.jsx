import {
  formatConfidence,
  formatRetrievalPct,
  confidencePhrase,
  confidenceDotColor,
  shouldShowRetrievalConfidence,
} from "../utils/displayHelpers.js";

export { shouldShowRetrievalConfidence };

export function ConfidenceBadge({
  confidence,
  retrievalScore,
  retrievedChunks,
  routedTo,
  modelId,
  t,
  ar = false,
  appearance = "field",
}) {
  if (
    !shouldShowRetrievalConfidence({
      routedTo,
      modelId,
      retrievedChunks,
      retrievalScore,
      confidence,
    })
  ) {
    return null;
  }

  const isRag =
    modelId &&
    modelId !== "base_llm" &&
    (routedTo || modelId) !== "base_llm";
  const pct = formatRetrievalPct(retrievalScore);
  const phrase = confidencePhrase(confidence, ar);
  const dotColor = confidenceDotColor(confidence, t);
  const isField = appearance === "field";

  const label = ar ? "ثقة الإجابة" : "Confidence";
  const matchLabel = ar ? "تطابق الاسترجاع" : "Retrieval match";
  const chunksLabel = ar ? "مقاطع" : "chunks";

  const wrapStyle = isField
    ? {
        marginTop: 10,
        padding: "8px 12px",
        borderRadius: 10,
        background: t.confidenceBg || t.bgHover,
        border: `1px solid ${t.border2}`,
      }
    : { marginTop: 10 };

  return (
    <div
      style={{
        ...wrapStyle,
        fontSize: 12,
        color: t.text3,
        lineHeight: 1.5,
        direction: ar ? "rtl" : "ltr",
        textAlign: ar ? "right" : "left",
      }}
      title={
        ar
          ? "أعلى = تطابق أقوى بين سؤالك ومقاطع قاعدة المعرفة"
          : "How well retrieved documents match your question"
      }
    >
      <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
        <span
          style={{
            width: 8,
            height: 8,
            borderRadius: "50%",
            background: dotColor,
            flexShrink: 0,
          }}
        />
        <span style={{ color: t.text2, fontWeight: isField ? 500 : 400 }}>
          {phrase}
        </span>
      </div>
      <div style={{ marginTop: 4, paddingLeft: isField ? 0 : 16 }}>
        <span style={{ color: t.text3 }}>
          {label}: <strong>{formatConfidence(confidence)}</strong>
        </span>
        {isRag && pct && (
          <span>
            {" "}
            · {matchLabel}: <strong>{pct}</strong>
            {retrievedChunks != null && retrievedChunks > 0
              ? ` · ${retrievedChunks} ${chunksLabel}`
              : ""}
          </span>
        )}
        {isRag && !pct && retrievedChunks > 0 && (
          <span>
            {" "}
            · {retrievedChunks} {chunksLabel}
          </span>
        )}
      </div>
    </div>
  );
}
