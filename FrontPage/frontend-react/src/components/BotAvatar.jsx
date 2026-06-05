import logoWhiteSrc from "@assets/logo/TM_Logo_white.png";
import { buildLogoFilter } from "./TerraLogo.jsx";
import { DEFAULT_LOGO_AVATAR_SCALE } from "../theme/visuals.js";

/** TerraMind logo avatar — white asset tinted per appearance theme. */
export function BotAvatar({
  t,
  size = 28,
  logoFilter = "none",
  logoGlow,
  logoTint,
  logoAvatarScale = DEFAULT_LOGO_AVATAR_SCALE,
}) {
  const ring = t.avatarRing || t.accentDim;
  const filter = buildLogoFilter(logoFilter, logoGlow);
  const tint = logoTint || t.accent;
  const logoSize = Math.round(size * logoAvatarScale);

  return (
    <div
      style={{
        width: size,
        height: size,
        borderRadius: "50%",
        background: ring,
        border: `1px solid ${t.border1}`,
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        flexShrink: 0,
        overflow: "hidden",
        boxShadow: `0 0 0 1px ${t.accentDim}, 0 2px 8px rgba(0,0,0,0.15)`,
      }}
      aria-hidden
    >
      <div
        className="tm-logo-mask"
        style={{
          width: logoSize,
          height: logoSize,
          flexShrink: 0,
          backgroundColor: tint,
          WebkitMaskImage: `url(${logoWhiteSrc})`,
          maskImage: `url(${logoWhiteSrc})`,
          WebkitMaskSize: "contain",
          maskSize: "contain",
          WebkitMaskRepeat: "no-repeat",
          maskRepeat: "no-repeat",
          WebkitMaskPosition: "center",
          maskPosition: "center",
          filter,
        }}
      />
    </div>
  );
}
