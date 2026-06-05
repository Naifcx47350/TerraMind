import { getRoutedDisplay } from "../settings/modelLabels.js";

export function RoutePill({ routedTo, routerReason, t, developerLabels, ar }) {
  if (!routedTo) return null;
  const { label, friendly, technical } = getRoutedDisplay(routedTo, {
    developerLabels,
  });

  return (
    <div
      style={{
        display: "inline-flex",
        flexDirection: "column",
        gap: 2,
        marginTop: 4,
        marginBottom: 4,
        direction: ar ? "rtl" : "ltr",
      }}
    >
      <span
        style={{
          display: "inline-block",
          fontSize: 11,
          color: t.text3,
          background: t.accentDim,
          border: `1px solid ${t.border1}`,
          borderRadius: 999,
          padding: "3px 10px",
          lineHeight: 1.4,
        }}
        title={routerReason || ""}
      >
        {ar ? "تمت الإجابة باستخدام" : "Answered using"}:{" "}
        <strong style={{ color: t.accent }}>{label}</strong>
      </span>
      {developerLabels && technical !== friendly && (
        <span style={{ fontSize: 10, color: t.text4, paddingLeft: 4 }}>
          {technical}
        </span>
      )}
    </div>
  );
}
