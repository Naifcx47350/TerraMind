import { MarkdownMessage } from "../MarkdownMessage.jsx";
import { splitAdvisorySections } from "../utils/advisorySections.js";

export function AdvisoryPanels({
  answer,
  t,
  ar = false,
  appearance = "classic",
  streaming = false,
}) {
  const { general, product, bothNonEmpty } = splitAdvisorySections(answer);

  if (!bothNonEmpty) {
    return (
      <MarkdownMessage content={answer} theme={t} dir={ar ? "rtl" : "ltr"} />
    );
  }

  const isField = appearance === "field";
  const panelStyle = (accentColor, kind) => ({
    background: t.bgCard,
    border: `1px solid ${t.border1}`,
    borderRadius: isField ? 14 : 12,
    overflow: "hidden",
    display: "flex",
    flexDirection: "column",
    minHeight: 80,
    borderLeft: isField ? `3px solid ${accentColor}` : undefined,
    className: isField
      ? `tm-advisory-panel tm-advisory-panel--${kind}`
      : undefined,
  });

  const panels = [
    {
      kind: "general",
      title: ar ? "إرشادات زراعية عامة" : "Public agriculture guidance",
      content: general,
      accent: t.panelGeneral || t.accent,
    },
    {
      kind: "product",
      title: ar ? "\u0643\u062a\u0627\u0644\u0648\u062c \u0627\u0644\u0645\u0646\u062a\u062c\u0627\u062a" : "Company product catalog",
      content: product,
      accent: t.panelProduct || t.accentWheat || "#c4a35a",
    },
  ];

  return (
    <div
      className="tm-advisory-grid"
      style={{
        display: "grid",
        gridTemplateColumns: "repeat(auto-fit, minmax(280px, 1fr))",
        gap: 12,
        alignItems: "stretch",
      }}
    >
      {panels.map(({ kind, title, content, accent }) => (
        <div
          key={kind}
          className={
            isField
              ? `tm-advisory-panel tm-advisory-panel--${kind}`
              : undefined
          }
          style={panelStyle(accent, kind)}
        >
          <div
            style={{
              padding: "10px 12px",
              borderBottom: `1px solid ${t.border1}`,
              background: t.bgSide,
              fontSize: 12,
              fontWeight: 600,
              color: t.text1,
              direction: ar ? "rtl" : "ltr",
              textAlign: ar ? "right" : "left",
            }}
          >
            {title}
          </div>
          <div
            style={{
              padding: "12px",
              fontSize: 14,
              flex: 1,
              direction: ar ? "rtl" : "ltr",
            }}
          >
            <MarkdownMessage
              content={content}
              theme={t}
              dir={ar ? "rtl" : "ltr"}
            />
            {streaming && kind === "product" && (
              <span
                style={{
                  display: "inline-block",
                  width: 8,
                  height: 14,
                  marginLeft: 2,
                  background: t.accent,
                  opacity: 0.7,
                  verticalAlign: "text-bottom",
                  animation: "blink 1s step-end infinite",
                }}
              />
            )}
          </div>
        </div>
      ))}
    </div>
  );
}

export function shouldUseAdvisoryPanels(model, answer) {
  if (model !== "advisory") return false;
  return splitAdvisorySections(answer).bothNonEmpty;
}
