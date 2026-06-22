import logoWhiteSrc from "@assets/logo/TM_Logo_white.png";

function buildLogoFilter(logoFilter = "none", logoGlow) {
  const parts = [
    logoFilter !== "none" ? logoFilter : "",
    logoGlow ? `drop-shadow(${logoGlow})` : "",
  ].filter(Boolean);
  return parts.length ? parts.join(" ") : undefined;
}

export function TerraLogo({
  size = 100,
  style = {},
  onSecretClick,
  logoFilter = "none",
  logoGlow,
  logoTint,
  className = "",
}) {
  const filter = buildLogoFilter(logoFilter, logoGlow);

  const graphic = (
    <div
      className={`tm-logo-mask ${className}`.trim()}
      role="img"
      aria-label="TerraMind"
      style={{
        width: size,
        height: size,
        backgroundColor: logoTint || "#10a37f",
        WebkitMaskImage: `url(${logoWhiteSrc})`,
        maskImage: `url(${logoWhiteSrc})`,
        WebkitMaskSize: "contain",
        maskSize: "contain",
        WebkitMaskRepeat: "no-repeat",
        maskRepeat: "no-repeat",
        WebkitMaskPosition: "center",
        maskPosition: "center",
        filter,
        ...style,
      }}
    />
  );

  if (!onSecretClick) return graphic;

  return (
    <button
      type="button"
      onClick={onSecretClick}
      aria-label="TerraMind"
      style={{
        background: "none",
        border: "none",
        padding: 0,
        margin: 0,
        cursor: "default",
        lineHeight: 0,
        display: "block",
      }}
    >
      {graphic}
    </button>
  );
}

export { buildLogoFilter, logoWhiteSrc };
