export const FIELD_DARK = {
  bg: "#0c0f0d",
  bgSide: "#121814",
  bgCard: "#1a211c",
  bgInput: "#1a211c",
  bgHover: "#242b26",
  bgActive: "#2d3630",
  accent: "#3d9b6a",
  accentDim: "rgba(61,155,106,0.14)",
  accentWheat: "#c4a35a",
  accentSoil: "#8b6914",
  accentSky: "#5a9ec4",
  text1: "#eef2ef",
  text2: "#c8d0cb",
  text3: "#8a968f",
  text4: "#5c665f",
  border1: "#2a332e",
  border2: "#1f2622",
  err: {
    bg: "rgba(220,80,60,0.09)",
    color: "#e07060",
    b: "rgba(220,80,60,0.22)",
  },
  btnText: "#ffffff",
  inputBorder: "#2a332e",
  inputFocus: "#3d9b6a",
  inputShadow: "rgba(61,155,106,0.18)",
  panelGeneral: "#3d9b6a",
  panelProduct: "#c4a35a",
  confidenceBg: "rgba(61,155,106,0.08)",
};

export const FIELD_LIGHT = {
  bg: "#faf9f6",
  bgSide: "#f2efe8",
  bgCard: "#ffffff",
  bgInput: "#ffffff",
  bgHover: "#ebe6dc",
  bgActive: "#e0d9cc",
  accent: "#2d7a52",
  accentDim: "rgba(45,122,82,0.1)",
  accentWheat: "#a8842e",
  accentSoil: "#6b5420",
  accentSky: "#4a8ab5",
  text1: "#1a1f1c",
  text2: "#3d4540",
  text3: "#6b736c",
  text4: "#9a9f9b",
  border1: "#d4cfc4",
  border2: "#e8e4db",
  err: { bg: "#fdecea", color: "#8b2820", b: "#f0b4b0" },
  btnText: "#ffffff",
  inputBorder: "#c8c2b6",
  inputFocus: "#2d7a52",
  inputShadow: "rgba(45,122,82,0.16)",
  panelGeneral: "#2d7a52",
  panelProduct: "#a8842e",
  confidenceBg: "rgba(45,122,82,0.06)",
};

export const FIELD_FONT =
  "'DM Sans', 'Segoe UI', system-ui, -apple-system, BlinkMacSystemFont, sans-serif";

export const FIELD_HEADING_FONT =
  "'DM Sans', 'Segoe UI', system-ui, -apple-system, sans-serif";

export const FIELD_TM_CSS = `
.tm-composer{border-radius:18px!important}
.tm-composer:focus-within{border-color:var(--tm-accent)!important;box-shadow:0 0 0 3px var(--tm-accent-dim),0 6px 24px rgba(0,0,0,.1)!important}
.tm-chip{border-radius:22px!important}
.tm-advisory-panel{border-radius:14px;overflow:hidden}
.tm-advisory-panel--general{border-left:3px solid var(--tm-panel-general)}
.tm-advisory-panel--product{border-left:3px solid var(--tm-panel-product)}
.tm-confidence-badge{padding:8px 12px;border-radius:10px;background:var(--tm-confidence-bg)}
.tm-empty-title{font-weight:800;letter-spacing:-0.02em}
.tm-bot-avatar-monogram{font-weight:700;font-size:11px;letter-spacing:-0.03em}
`;
