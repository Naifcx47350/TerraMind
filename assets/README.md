# TerraMind appearance assets

## PNG files (per theme)

```
assets/backgrounds/{appearance}/
  {appearance}_dark_mode.png    ← stylized wallpaper (dark UI)
  {appearance}_light_mode.png   ← stylized wallpaper (light UI) — add your 5 new files here
  {appearance}_wide.png         ← legacy wide fallback / artifact (optional)
  {appearance}_asset_0.png      welcome card (code defaults only)
  {appearance}_asset_1.png      profile avatar decor (Advanced settings)
  {appearance}_asset_2.png      empty state (reserved)
  {appearance}_asset_3.png      composer corner (Advanced settings)
```

**Naming migration:** former `{appearance}2.png` → `{appearance}_dark_mode.png`. Former `{appearance}.png` → `{appearance}_wide.png`.

If `{appearance}_light_mode.png` is missing, the app falls back to `{appearance}_dark_mode.png` until you add the light wallpaper.

---

## Default asset slots (profile + composer)

| Theme | Profile slot | Profile rotation | Composer slot | Composer rotation |
|-------|-------------|------------------|---------------|-------------------|
| Field | 2 | 0° | 0 | -10° |
| Forest | 1 | -50° | 2 | -27° |
| Harvest | 2 | 80° | 0 | -84° |
| Ocean | 2 | -25° | 0 | -107° |
| Dusk | 0 | -10° | 1 | -25° |

Advanced slider overrides are saved **per appearance** in localStorage (`decorTuning.field`, `.forest`, etc.).

---

## Code defaults — one file per theme

`FrontPage/frontend-react/src/theme/decorDefaults/{appearance}.js`

| Role | Keys | Advanced sliders? |
|------|------|-------------------|
| `welcome` | slot, opacity, rotation, top, insetEnd, width, height | No — fixed in theme file |
| `profile` | same | Yes — per appearance |
| `composer` | same | Yes — per appearance |

---

## Where assets render

| Role | Component |
|------|-----------|
| Background | `App.jsx` ambient layer (`resolveThemeBackground`) |
| Welcome | `SidebarWelcomeCard.jsx` |
| Profile | `UserProfileMenu.jsx` (corner on avatar) |
| Composer | `App.jsx` chat input (above the box) |
