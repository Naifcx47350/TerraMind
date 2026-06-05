import { useState } from "react";
import { tr } from "../i18n/strings.js";

export function SidebarWelcomeCard({ t, uiSettings, rtl, decorUrl, decorStyle }) {
  const [visible, setVisible] = useState(true);

  if (!visible) return null;

  return (
    <div
      className="tm-welcome-card"
      style={{
        position: "relative",
        marginBottom: 10,
        padding: "14px 14px 12px",
        borderRadius: 14,
        background: `linear-gradient(145deg, color-mix(in srgb, ${t.accent} 22%, ${t.bgCard}) 0%, ${t.bgCard} 55%)`,
        border: `1px solid color-mix(in srgb, ${t.accent} 35%, ${t.border1})`,
        boxShadow: `0 8px 24px rgba(0,0,0,0.18), inset 0 1px 0 rgba(255,255,255,0.05)`,
        textAlign: rtl ? "right" : "left",
        direction: rtl ? "rtl" : "ltr",
      }}
    >
      {decorUrl ? (
        <img
          src={decorUrl}
          alt=""
          aria-hidden
          className="tm-welcome-card-decor tm-decor-img tm-decor-fixed"
          style={decorStyle}
        />
      ) : (
        <span
          aria-hidden
          className="tm-welcome-card-emoji"
          style={{
            position: "absolute",
            top: -8,
            insetInlineEnd: 14,
            fontSize: 22,
            lineHeight: 1,
            filter: `drop-shadow(0 0 8px color-mix(in srgb, ${t.accent} 50%, transparent))`,
          }}
        >
          🌱
        </span>
      )}
      <div
        style={{
          fontSize: 13,
          fontWeight: 700,
          color: t.text1,
          lineHeight: 1.45,
          paddingInlineEnd: decorUrl ? 40 : 28,
        }}
      >
        {tr(uiSettings, "welcomeTitle")}
      </div>
      <div
        style={{
          fontSize: 11,
          color: t.text3,
          lineHeight: 1.5,
          marginTop: 6,
          paddingInlineEnd: 8,
        }}
      >
        {tr(uiSettings, "welcomeBody")}
      </div>
      <div
        style={{
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          marginTop: 10,
          flexDirection: rtl ? "row-reverse" : "row",
        }}
      >
        <button
          type="button"
          onClick={() => setVisible(false)}
          style={{
            fontSize: 11,
            fontWeight: 600,
            fontFamily: "inherit",
            color: t.accent,
            background: t.accentDim,
            border: `1px solid color-mix(in srgb, ${t.accent} 40%, transparent)`,
            borderRadius: 8,
            padding: "5px 10px",
            cursor: "pointer",
          }}
        >
          {tr(uiSettings, "welcomeDismiss")}
        </button>
        <button
          type="button"
          onClick={() => setVisible(false)}
          aria-label={tr(uiSettings, "welcomeDismiss")}
          title={tr(uiSettings, "welcomeDismiss")}
          style={{
            width: 28,
            height: 28,
            borderRadius: "50%",
            border: `1px solid ${t.border1}`,
            background: t.bgInput,
            color: t.text3,
            cursor: "pointer",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            fontFamily: "inherit",
            fontSize: 14,
            lineHeight: 1,
          }}
        >
          →
        </button>
      </div>
    </div>
  );
}
