import {
  CLASSIC_DARK,
  CLASSIC_LIGHT,
  CLASSIC_TM_CSS,
} from "./classic.js";
import {
  FIELD_DARK,
  FIELD_LIGHT,
  FIELD_FONT,
  FIELD_HEADING_FONT,
  FIELD_TM_CSS,
} from "./field.js";
import {
  HARVEST_DARK,
  HARVEST_LIGHT,
  HARVEST_FONT,
  HARVEST_TM_CSS,
} from "./harvest.js";
import {
  OCEAN_DARK,
  OCEAN_LIGHT,
  OCEAN_FONT,
  OCEAN_TM_CSS,
} from "./ocean.js";
import {
  DUSK_DARK,
  DUSK_LIGHT,
  DUSK_FONT,
  DUSK_TM_CSS,
} from "./dusk.js";
import { THEME_VISUALS, DECORATIVE_CSS, DEFAULT_LOGO_AVATAR_SCALE } from "./visuals.js";

export const APPEARANCE_OPTIONS = [
  { id: "field", swatch: "#10a37f", usesDmSans: true },
  { id: "forest", swatch: "#3d9b6a", usesDmSans: true },
  { id: "harvest", swatch: "#d4a017", usesDmSans: true },
  { id: "ocean", swatch: "#3a9ec4", usesDmSans: true },
  { id: "dusk", swatch: "#9b7ed4", usesDmSans: true },
];

const THEME_MAP = {
  field: {
    dark: CLASSIC_DARK,
    light: CLASSIC_LIGHT,
    font: FIELD_FONT,
    headingFont: FIELD_HEADING_FONT,
    extraCss: "",
    chipRadius: 20,
    composerRadius: 16,
  },
  forest: {
    dark: FIELD_DARK,
    light: FIELD_LIGHT,
    font: FIELD_FONT,
    headingFont: FIELD_HEADING_FONT,
    extraCss: FIELD_TM_CSS,
    chipRadius: 22,
    composerRadius: 18,
  },
  harvest: {
    dark: HARVEST_DARK,
    light: HARVEST_LIGHT,
    font: HARVEST_FONT,
    headingFont: HARVEST_FONT,
    extraCss: HARVEST_TM_CSS,
    chipRadius: 22,
    composerRadius: 18,
  },
  ocean: {
    dark: OCEAN_DARK,
    light: OCEAN_LIGHT,
    font: OCEAN_FONT,
    headingFont: OCEAN_FONT,
    extraCss: OCEAN_TM_CSS,
    chipRadius: 22,
    composerRadius: 18,
  },
  dusk: {
    dark: DUSK_DARK,
    light: DUSK_LIGHT,
    font: DUSK_FONT,
    headingFont: DUSK_FONT,
    extraCss: DUSK_TM_CSS,
    chipRadius: 22,
    composerRadius: 18,
  },
};

function boostStylizedContrast(t, dark) {
  if (dark) {
    return {
      ...t,
      text2: t.text1,
      text3: t.text2,
    };
  }
  return {
    ...t,
    text1: "#0a0a0a",
    text2: "#161616",
    text3: "#404040",
    text4: "#5c5c5c",
  };
}

export function resolveTheme(appearance, dark, options = {}) {
  const { stylized = false } = options;
  const key = THEME_MAP[appearance] ? appearance : "field";
  const row = THEME_MAP[key];
  const visuals = THEME_VISUALS[key] || THEME_VISUALS.field;
  const base = dark ? row.dark : row.light;
  const t = stylized ? boostStylizedContrast(base, dark) : base;
  const css = `${CLASSIC_TM_CSS}\n${DECORATIVE_CSS}${row.extraCss ? `\n${row.extraCss}` : ""}`;

  return {
    t: {
      ...t,
      avatarRing: t.avatarRing || t.accentDim,
    },
    fontFamily: row.font,
    headingFont: row.headingFont,
    css,
    appearance: key,
    chipRadius: row.chipRadius,
    composerRadius: row.composerRadius,
    usesDmSans: true,
    logoFilter: visuals.logoFilter,
    logoGlow: visuals.logoGlow,
    logoVariant: visuals.logoVariant || "white",
    logoTint: visuals.logoTint || t.accent,
    logoAvatarScale: visuals.logoAvatarScale ?? DEFAULT_LOGO_AVATAR_SCALE,
    ambientBackground: dark ? visuals.ambientDark : visuals.ambientLight,
  };
}

export function appearanceUsesDmSans() {
  return true;
}
