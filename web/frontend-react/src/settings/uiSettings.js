import {
  APPEARANCE_IDS,
  buildDefaultDecorTuningByAppearance,
  defaultDecorTuningForAppearance,
} from "../theme/decorDefaults/index.js";

const UI_SETTINGS_KEY = "terramind_ui_settings_v2";
const LEGACY_SETTINGS_KEY = "terramind_ui_settings_v1";
const LEGACY_SCORES_KEY = "terramind_show_scores_v1";

export { buildDefaultDecorTuningByAppearance as DEFAULT_DECOR_TUNING_BY_APPEARANCE };

export const DEFAULT_UI_SETTINGS = {
  appearance: "field",
  language: "en",
  profileName: "Developer",
  developerLabels: false,
  showSources: false,
  showConfidence: false,
  stylizedLayout: true,
  decorTuning: buildDefaultDecorTuningByAppearance(),
};

function isPerAppearanceDecorTuning(obj) {
  return (
    obj &&
    typeof obj === "object" &&
    typeof obj.field === "object" &&
    obj.field.profile
  );
}

function mergeRoleTuning(defaults, saved) {
  return {
    profile: { ...defaults.profile, ...saved?.profile },
    composer: { ...defaults.composer, ...saved?.composer },
  };
}

function mergeDecorTuningByAppearance(parsed, appearance) {
  const defaults = buildDefaultDecorTuningByAppearance();

  if (isPerAppearanceDecorTuning(parsed)) {
    const out = { ...defaults };
    for (const id of APPEARANCE_IDS) {
      if (parsed[id]) {
        out[id] = mergeRoleTuning(defaults[id], parsed[id]);
      }
    }
    return out;
  }

  if (parsed?.profile || parsed?.composer) {
    const app = APPEARANCE_IDS.includes(appearance) ? appearance : "field";
    return {
      ...defaults,
      [app]: mergeRoleTuning(defaults[app], parsed),
    };
  }

  return defaults;
}

function migrateLegacyAppearance(appearance) {
  if (appearance === "classic") return "field";
  if (appearance === "field") return "forest";
  return appearance;
}

function normalizeSettings(parsed) {
  const version = parsed._v ?? 1;
  let appearance = parsed.appearance ?? DEFAULT_UI_SETTINGS.appearance;
  if (version < 2) {
    appearance = migrateLegacyAppearance(appearance);
  }
  return {
    ...DEFAULT_UI_SETTINGS,
    ...parsed,
    _v: 3,
    appearance,
    decorTuning: mergeDecorTuningByAppearance(parsed.decorTuning, appearance),
  };
}

export function getDecorTuningForAppearance(settings, appearance) {
  const app = APPEARANCE_IDS.includes(appearance) ? appearance : "field";
  const byApp = settings?.decorTuning;
  if (byApp?.[app]?.profile) {
    return mergeRoleTuning(defaultDecorTuningForAppearance(app), byApp[app]);
  }
  if (byApp?.profile || byApp?.composer) {
    return mergeRoleTuning(
      defaultDecorTuningForAppearance(app),
      byApp,
    );
  }
  return defaultDecorTuningForAppearance(app);
}

export function loadUiSettings() {
  try {
    const raw =
      localStorage.getItem(UI_SETTINGS_KEY) ||
      localStorage.getItem(LEGACY_SETTINGS_KEY);
    if (raw) {
      return normalizeSettings(JSON.parse(raw));
    }
  } catch {
    /* ignore */
  }

  const legacyScores = localStorage.getItem(LEGACY_SCORES_KEY) === "1";
  return { ...DEFAULT_UI_SETTINGS, showConfidence: legacyScores };
}

export function saveUiSettings(settings) {
  try {
    localStorage.setItem(
      UI_SETTINGS_KEY,
      JSON.stringify({ ...settings, _v: 3 }),
    );
    localStorage.setItem(
      LEGACY_SCORES_KEY,
      settings.showConfidence ? "1" : "0",
    );
  } catch {
    /* quota or private mode */
  }
}

export function patchUiSettings(patch) {
  const next = { ...loadUiSettings(), ...patch };
  saveUiSettings(next);
  return next;
}
