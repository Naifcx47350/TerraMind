const UI_SETTINGS_KEY = "terramind_ui_settings_v1";
const LEGACY_SCORES_KEY = "terramind_show_scores_v1";

export const DEFAULT_UI_SETTINGS = {
  appearance: "classic",
  developerLabels: false,
  showSources: false,
  showConfidence: false,
};

export function loadUiSettings() {
  try {
    const raw = localStorage.getItem(UI_SETTINGS_KEY);
    if (raw) {
      const parsed = JSON.parse(raw);
      return { ...DEFAULT_UI_SETTINGS, ...parsed };
    }
  } catch {
    /* ignore */
  }

  const legacyScores = localStorage.getItem(LEGACY_SCORES_KEY) === "1";
  return { ...DEFAULT_UI_SETTINGS, showConfidence: legacyScores };
}

export function saveUiSettings(settings) {
  try {
    localStorage.setItem(UI_SETTINGS_KEY, JSON.stringify(settings));
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
