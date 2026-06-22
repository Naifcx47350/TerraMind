# TerraMind UI assets & customization

Guide for changing wallpapers, decor art, theme defaults, and user-facing settings.

---

## Folder layout

```
assets/backgrounds/{appearance}/
  {appearance}_dark_mode.png     stylized wallpaper (dark UI)
  {appearance}_light_mode.png    stylized wallpaper (light UI)
  {appearance}_wide.png          optional legacy wide fallback
  {appearance}_asset_0.png       welcome card (fixed defaults)
  {appearance}_asset_1.png       profile avatar decor
  {appearance}_asset_2.png       empty state (reserved, not wired yet)
  {appearance}_asset_3.png       composer corner decor
```

**Appearances:** `field`, `forest`, `harvest`, `ocean`, `dusk`

After adding or renaming PNGs, restart the Vite dev server (or run `npm run build`) so `import.meta.glob` picks up new files. In Docker, rebuild the `frontend` image after asset changes (`docker compose build frontend`).

---

## What to change where

| Goal | Edit |
|------|------|
| Replace dark/light wallpaper | Drop PNG in `assets/backgrounds/{appearance}/` with names above |
| Default decor slot / rotation / position (per theme) | `web/frontend-react/src/theme/decorDefaults/{appearance}.js` |
| Text colors (dark/light palettes) | `web/frontend-react/src/theme/{appearance}.js` or `classic.js` (Field uses classic tokens) |
| Ambient gradients, glass CSS, sidebar width | `web/frontend-react/src/theme/visuals.js` |
| Which wallpaper loads | `web/frontend-react/src/theme/backgroundAssets.js` → `resolveThemeBackground()` |
| Advanced slider labels / i18n | `web/frontend-react/src/i18n/strings.js` |
| Per-user decor overrides (saved) | Browser `localStorage` key `terramind_ui_settings_v2` → `decorTuning.{appearance}` |
| Theme swatches / appearance list | `web/frontend-react/src/theme/index.js` → `APPEARANCE_OPTIONS` |
| Welcome card copy | `web/frontend-react/src/i18n/strings.js` |
| Sidebar width constant | `web/frontend-react/src/App.jsx` → `SIDEBAR_WIDTH` |

Full UI customization index: [../docs/UI_CUSTOMIZATION.md](../docs/UI_CUSTOMIZATION.md)

---

## Wallpapers

| File | Used when |
|------|-----------|
| `{appearance}_dark_mode.png` | Stylized layout + dark mode |
| `{appearance}_light_mode.png` | Stylized layout + light mode |
| `{appearance}_wide.png` | Fallback only if mode file missing |

Resolution: use tall portrait art (same aspect as former `*2.png` files). Wide files are legacy artifacts.

---

## Decor roles

| Slot | Role | Advanced sliders? | Component |
|------|------|-------------------|-----------|
| 0 | Welcome card | No | `SidebarWelcomeCard.jsx` |
| 1 | Profile avatar badge | Yes (per appearance) | `UserProfileMenu.jsx` |
| 2 | Empty state | Reserved | — |
| 3 | Composer corner | Yes (per appearance) | `App.jsx` input footer |

**Default slots & rotations** (code defaults in `decorDefaults/*.js`):

| Theme | Profile | Composer |
|-------|---------|----------|
| Field | slot 2 | slot 0, -10° |
| Forest | slot 1, -50° | slot 2, -27° |
| Harvest | slot 2, 80° | slot 0, -84° |
| Ocean | slot 2, -25° | slot 0, -107° |
| Dusk | slot 0, -10° | slot 1, -25° |

Each decor role in `decorDefaults/{theme}.js` supports:

```js
{
  slot: 0,           // 0–3 → {appearance}_asset_N.png
  opacity: 1,
  rotation: 0,       // degrees
  top: -28,          // px from top of anchor
  insetEnd: -18,     // px from inline-end corner (RTL-aware)
  width: 88,
  height: 88,
}
```

Settings → Layout → **Advanced** saves **slot, opacity, rotation only** per appearance under `decorTuning.field`, `.forest`, etc. Position/size always come from the theme file unless you edit that file.

---

## User settings (localStorage)

Key: `terramind_ui_settings_v2` (schema `_v: 3`)

| Field | Purpose |
|-------|---------|
| `appearance` | Active theme id |
| `stylizedLayout` | `true` = background + decor; `false` = flat/simple |
| `decorTuning.{appearance}.profile` | User slot/opacity/rotation for profile |
| `decorTuning.{appearance}.composer` | User slot/opacity/rotation for composer |
| `developerLabels`, `showSources`, `showConfidence` | Debug / metadata toggles |
| `language` | `en` \| `ar` |

To reset decor to code defaults: remove `decorTuning` from stored JSON or clear the key.

---

## Layout modes

| Mode | Background | Decor | Text |
|------|------------|-------|------|
| **Stylized** | `{appearance}_{dark\|light}_mode.png` | Profile + composer + welcome | Boosted contrast + scrim over messages |
| **Simple** | CSS ambient gradient only | Hidden | Standard theme tokens |

Composer corner asset renders **above** the glass input box (`z-index` in `visuals.js`).

---

## Adding a new appearance (checklist)

1. Add swatch in `theme/index.js` → `APPEARANCE_OPTIONS` + `THEME_MAP` (dark/light tokens, font, CSS).
2. Add `theme/{name}.js` palette + optional `theme/decorDefaults/{name}.js`.
3. Register decor in `theme/decorDefaults/index.js` → `THEME_DECOR`.
4. Add `assets/backgrounds/{name}/` with wallpapers + `_asset_0..3.png`.
5. Add i18n label `themes.{name}` in `i18n/strings.js`.
6. Add default entry in `buildDefaultDecorTuningByAppearance()` via new decor file.

---

## Naming history (avoid conflicts)

| Old name | Current name |
|----------|----------------|
| `{theme}2.png`, `{Theme}2.png` | `{theme}_dark_mode.png` |
| `{theme}.png`, `{Theme}.png` | `{theme}_wide.png` |
| `classic` appearance | `field` |
| old `field` appearance | `forest` |

Legacy names are still resolved as fallbacks in `backgroundAssets.js` but should not be used for new art.
