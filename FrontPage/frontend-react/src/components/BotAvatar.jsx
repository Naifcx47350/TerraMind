import logoSrc from "@assets/logo/TM_Logo.png";

export function BotAvatar({ t, useMonogram, size = 28 }) {
  if (useMonogram) {
    return (
      <div
        className="tm-bot-avatar-monogram"
        style={{
          width: size,
          height: size,
          borderRadius: "50%",
          background: t.accentDim,
          border: `1px solid ${t.border1}`,
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          flexShrink: 0,
          color: t.accent,
          fontSize: Math.round(size * 0.38),
          fontWeight: 700,
          letterSpacing: "-0.03em",
        }}
        aria-hidden
      >
        TM
      </div>
    );
  }

  return (
    <div
      style={{
        width: size,
        height: size,
        borderRadius: "50%",
        background: t.accentDim,
        border: `1px solid ${t.border1}`,
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        flexShrink: 0,
        overflow: "hidden",
      }}
    >
      <img
        src={logoSrc}
        alt=""
        width={size + 2}
        height={size + 2}
        style={{ objectFit: "contain", display: "block" }}
      />
    </div>
  );
}
