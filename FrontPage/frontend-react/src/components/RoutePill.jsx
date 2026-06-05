import { getRoutedDisplay } from "../settings/modelLabels.js";

export function RoutePill({
  routedTo,
  routerReason,
  t,
  developerLabels,
  ar,
  language = "en",
  answeredUsingLabel,
}) {
  if (!routedTo) return null;
  const { friendly, technical } = getRoutedDisplay(routedTo, {
    developerLabels,
    language,
  });
  const modeName = friendly;

  const prefix =
    answeredUsingLabel || (ar ? "تمت الإجابة باستخدام" : "Answered using");

  return (
    <div
      style={{
        display: "inline-flex",
        flexDirection: "column",
        gap: 2,
        marginTop: 4,
        marginBottom: 4,
      }}
    >
      <span
        style={{
          display: "inline-flex",
          alignItems: "center",
          flexWrap: "wrap",
          gap: 6,
          fontSize: 11,
          color: t.text3,
          background: t.accentDim,
          border: `1px solid ${t.border1}`,
          borderRadius: 999,
          padding: "3px 10px",
          lineHeight: 1.4,
          direction: ar ? "rtl" : "ltr",
          unicodeBidi: "isolate",
        }}
        title={routerReason || ""}
      >
        <span>{prefix}</span>
        <strong
          style={{ color: t.accent, unicodeBidi: "isolate" }}
          dir="auto"
        >
          {modeName}
        </strong>
      </span>
      {developerLabels && technical && (
        <span
          style={{
            fontSize: 10,
            color: t.text3,
            direction: "ltr",
            unicodeBidi: "isolate",
            paddingInlineStart: 2,
          }}
        >
          {technical}
        </span>
      )}
    </div>
  );
}
