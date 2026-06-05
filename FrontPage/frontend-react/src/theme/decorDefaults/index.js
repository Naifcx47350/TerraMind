/**
 * Per-theme decor defaults — one file per appearance.
 *
 * Edit the file for your theme:
 *   decorDefaults/field.js | forest.js | harvest.js | ocean.js | dusk.js
 *
 * Each role supports: slot (0–3), opacity, rotation (deg),
 * top, insetEnd (px from corner), width, height.
 *
 * Settings → Advanced overrides (profile + composer only) saved per appearance.
 */

import { FIELD_DECOR } from "./field.js";
import { FOREST_DECOR } from "./forest.js";
import { HARVEST_DECOR } from "./harvest.js";
import { OCEAN_DECOR } from "./ocean.js";
import { DUSK_DECOR } from "./dusk.js";

export const APPEARANCE_IDS = ["field", "forest", "harvest", "ocean", "dusk"];

export const THEME_DECOR = {
  field: FIELD_DECOR,
  forest: FOREST_DECOR,
  harvest: HARVEST_DECOR,
  ocean: OCEAN_DECOR,
  dusk: DUSK_DECOR,
};

export const DEFAULT_ASSET_SLOTS = {
  welcome: 0,
  profile: 1,
  empty: 2,
  composer: 3,
};

export const DEFAULT_BACKGROUND_LAYOUT = {
  imagePosition: "center bottom",
  size: "cover",
};

export const DEFAULT_DECOR_BLEND = {
  mixBlendMode: "screen",
  dropShadow: "0 0 14px color-mix(in srgb, var(--tm-accent) 45%, transparent)",
};

/** Saved-settings shape (opacity / rotation / slot only). */
export function defaultDecorTuningForAppearance(appearance = "field") {
  const theme = THEME_DECOR[appearance] ?? THEME_DECOR.field;
  return {
    profile: {
      slot: theme.profile?.slot ?? 1,
      opacity: theme.profile?.opacity ?? 1,
      rotation: theme.profile?.rotation ?? 0,
    },
    composer: {
      slot: theme.composer.slot,
      opacity: theme.composer.opacity,
      rotation: theme.composer.rotation,
    },
  };
}

export function buildDefaultDecorTuningByAppearance() {
  return Object.fromEntries(
    APPEARANCE_IDS.map((id) => [id, defaultDecorTuningForAppearance(id)]),
  );
}

/** @deprecated Use buildDefaultDecorTuningByAppearance() or defaultDecorTuningForAppearance() */
export const DEFAULT_DECOR_TUNING = defaultDecorTuningForAppearance("field");

export function getThemeDecorDefaults(appearance) {
  return THEME_DECOR[appearance] ?? THEME_DECOR.field;
}

export function getDecorRoleDefaults(appearance, role) {
  return getThemeDecorDefaults(appearance)[role] ?? {};
}

/** Theme file defaults merged with user slider overrides. */
export function mergeDecorRole(appearance, role, userTuning = {}) {
  return { ...getDecorRoleDefaults(appearance, role), ...userTuning };
}
