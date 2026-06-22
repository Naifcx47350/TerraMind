import { DEFAULT_ASSET_SLOTS, mergeDecorRole } from "./decorDefaults/index.js";

/**
 * Per-appearance assets under assets/backgrounds/{appearance}/.
 *
 * Wallpapers (stylized layout):
 *   {appearance}_dark_mode.png   — full-height stylized background (dark UI)
 *   {appearance}_light_mode.png  — full-height stylized background (light UI)
 *   {appearance}_wide.png        — legacy wide fallback / artifact
 *
 * Decor slots:
 *   {appearance}_asset_0..3.png
 */

const ASSET_GLOB = import.meta.glob(
  "@assets/backgrounds/**/*.{png,jpg,jpeg,webp,svg}",
  {
    eager: true,
    import: "default",
  },
);

export const APPEARANCES = ["field", "forest", "harvest", "ocean", "dusk"];

/** @deprecated use DEFAULT_ASSET_SLOTS from decorDefaults.js */
export const ASSET_SLOT = DEFAULT_ASSET_SLOTS;

export const ASSET_SLOT_LABELS = {
  0: "Asset 0 (welcome)",
  1: "Asset 1 (profile)",
  2: "Asset 2 (empty state)",
  3: "Asset 3 (composer)",
};

function normalizePath(key) {
  return key.replace(/\\/g, "/").toLowerCase();
}

function fileName(key) {
  const base = normalizePath(key).split("/").pop() || "";
  return base.replace(/\.[^.]+$/, "");
}

function appearanceEntries(appearance) {
  return Object.entries(ASSET_GLOB).filter(([key]) =>
    normalizePath(key).includes(`/backgrounds/${appearance}/`),
  );
}

function pickByNames(entries, names) {
  for (const name of names) {
    if (!name) continue;
    const want = name.toLowerCase();
    const hit = entries.find(([key]) => fileName(key) === want);
    if (hit) return hit[1];
  }
  return null;
}

function isWallpaperFile(fn) {
  return (
    fn.endsWith("_dark_mode") ||
    fn.endsWith("_light_mode") ||
    fn.endsWith("_wide") ||
    fn.endsWith("_fallback_wide") ||
    fn.endsWith("2")
  );
}

function isNumberedAsset(fn) {
  return /_(asset|decor)_\d+$/.test(fn);
}

function assetSlotUrl(entries, appearance, slot) {
  const prefix = `${appearance}_asset_${slot}`;
  return pickByNames(entries, [prefix]);
}

/** @returns {string|null} */
export function resolveThemeBackground(appearance, dark) {
  const entries = appearanceEntries(appearance);
  if (!entries.length) return null;

  const primary = dark
    ? `${appearance}_dark_mode`
    : `${appearance}_light_mode`;

  const themed = pickByNames(entries, [primary]);
  if (themed) return themed;

  if (!dark) {
    const darkFallback = pickByNames(entries, [`${appearance}_dark_mode`]);
    if (darkFallback) return darkFallback;
  }

  const cap = appearance.charAt(0).toUpperCase() + appearance.slice(1);
  const legacyTall = pickByNames(entries, [
    `${appearance}2`,
    `${cap}2`,
    "background2",
    "background-tall",
  ]);
  if (legacyTall) return legacyTall;

  const wide = pickByNames(entries, [
    `${appearance}_wide`,
    `${appearance}_fallback_wide`,
    appearance,
    cap,
  ]);
  if (wide) return wide;

  const bgCandidates = entries.filter(([key]) => {
    const fn = fileName(key);
    if (isNumberedAsset(fn)) return false;
    if (fn === "dark" || fn === "light") return false;
    if (isWallpaperFile(fn)) return false;
    return true;
  });

  return bgCandidates[0]?.[1] ?? null;
}

/**
 * @param {"welcome"|"profile"|"composer"|"sidebar"|"empty"} role
 * @param {{ slot?: number }} [opts] — slot overrides default ASSET_SLOT[role]
 * @returns {string|null}
 */
export function resolveAppearanceAsset(appearance, role, { slot } = {}) {
  const entries = appearanceEntries(appearance);
  if (!entries.length) return null;

  const slotNum = slot ?? DEFAULT_ASSET_SLOTS[role];
  if (slotNum != null) {
    const bySlot = assetSlotUrl(entries, appearance, slotNum);
    if (bySlot) return bySlot;
  }

  const legacy = {
    welcome: ["welcome", "welcome-decor"],
    profile: ["profile", "profile-decor", "avatar-decor"],
    composer: ["composer", "composer-decor"],
    sidebar: ["sidebar", "sidebar-decor"],
    empty: ["empty", "empty-decor"],
  };
  return pickByNames(entries, legacy[role] ?? []);
}

/** Inline style for a decor image (fixed px size, theme defaults + user tuning). */
export function decorImageStyle(role, userTuning, appearance = "field") {
  const d = mergeDecorRole(appearance, role, userTuning);
  const w = d.width ?? 44;
  const h = d.height ?? 44;
  return {
    position: "absolute",
    top: d.top ?? 0,
    insetInlineEnd: d.insetEnd ?? 0,
    width: w,
    height: h,
    minWidth: w,
    maxWidth: w,
    minHeight: h,
    maxHeight: h,
    objectFit: "contain",
    pointerEvents: "none",
    opacity: d.opacity ?? 1,
    transform: `rotate(${d.rotation ?? 0}deg)`,
  };
}

/** @deprecated use decorImageStyle */
export function decorTransformStyle(tuning) {
  if (!tuning) return {};
  return {
    opacity: tuning.opacity ?? 1,
    transform: `rotate(${tuning.rotation ?? 0}deg)`,
  };
}

export function resolveAppearanceBundle(
  appearance,
  { stylized = false, dark = true, decorTuning } = {},
) {
  const profileSlot = decorTuning?.profile?.slot;
  const composerSlot = decorTuning?.composer?.slot;
  return {
    background: stylized ? resolveThemeBackground(appearance, dark) : null,
    welcome: resolveAppearanceAsset(appearance, "welcome"),
    profile: stylized
      ? resolveAppearanceAsset(appearance, "profile", { slot: profileSlot })
      : null,
    composer: stylized
      ? resolveAppearanceAsset(appearance, "composer", { slot: composerSlot })
      : null,
    sidebar: stylized ? resolveAppearanceAsset(appearance, "sidebar") : null,
    empty: stylized ? resolveAppearanceAsset(appearance, "empty") : null,
  };
}
