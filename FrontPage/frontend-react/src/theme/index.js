import {
  CLASSIC_DARK,
  CLASSIC_LIGHT,
  CLASSIC_FONT,
  CLASSIC_TM_CSS,
} from "./classic.js";
import {
  FIELD_DARK,
  FIELD_LIGHT,
  FIELD_FONT,
  FIELD_HEADING_FONT,
  FIELD_TM_CSS,
} from "./field.js";

export function resolveTheme(appearance, dark) {
  const isField = appearance === "field";
  const t = dark
    ? isField
      ? FIELD_DARK
      : CLASSIC_DARK
    : isField
      ? FIELD_LIGHT
      : CLASSIC_LIGHT;

  const fontFamily = isField ? FIELD_FONT : CLASSIC_FONT;
  const headingFont = isField ? FIELD_HEADING_FONT : CLASSIC_FONT;
  const css = isField
    ? `${CLASSIC_TM_CSS}\n${FIELD_TM_CSS}`
    : CLASSIC_TM_CSS;

  return {
    t,
    fontFamily,
    headingFont,
    css,
    appearance,
    useMonogramAvatar: isField,
    chipRadius: isField ? 22 : 20,
    composerRadius: isField ? 18 : 16,
  };
}
