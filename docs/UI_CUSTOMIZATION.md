# UI customization (frontend)

Quick index for TerraMind chat UI theming. Asset filenames and decor slots: **[../assets/README.md](../assets/README.md)**.

---

## Source files

```
FrontPage/frontend-react/src/
├── App.jsx                      Shell, sidebar, composer, message layout
├── settings/uiSettings.js       localStorage schema, decorTuning per appearance
├── theme/
│   ├── index.js                 resolveTheme(), APPEARANCE_OPTIONS
│   ├── classic.js               Field appearance tokens + base CSS animations
│   ├── field.js … dusk.js       Forest/Harvest/Ocean/Dusk palettes
│   ├── visuals.js               Glass, scrims, sidebar blur, composer z-index
│   ├── backgroundAssets.js      Wallpaper + decor PNG resolution
│   └── decorDefaults/           Per-theme decor position & default slots
├── components/
│   ├── SettingsMenuContent.jsx  Appearance, layout, advanced decor sliders
│   ├── SidebarWelcomeCard.jsx   Welcome card + asset 0
│   └── UserProfileMenu.jsx      Profile decor on avatar
└── i18n/strings.js              Labels (EN / AR)
```

---

## Common tasks

### Change wallpaper for one theme

1. Replace `assets/backgrounds/{theme}/{theme}_dark_mode.png` and/or `{theme}_light_mode.png`.
2. Keep the same filename; no code change required.

### Tweak composer flower position (all users of that theme)

Edit `theme/decorDefaults/{theme}.js` → `composer: { top, insetEnd, width, height, rotation, slot }`.

### Let users pick a different asset slot

Defaults come from decor files; users override via **Settings → Advanced** (saved per appearance in `decorTuning`).

### Improve text readability on stylized backgrounds

- Palette: bump `text2`–`text4` in `theme/*.js`
- Stylized boost: `theme/index.js` → `boostStylizedContrast()`
- CSS scrim/shadow: `theme/visuals.js` → `.tm-stylized .tm-content-width`

### Widen sidebar (conversation list clipping)

`App.jsx` → `SIDEBAR_WIDTH` (currently 280px).

---

## Settings migration

| Version | Change |
|---------|--------|
| v1 → v2 | `classic`→`field`, old `field`→`forest` |
| v2 → v3 | Global `decorTuning` → per-appearance `decorTuning.field`, `.forest`, … |

Stored key: `terramind_ui_settings_v2` (internal `_v: 3`).

---

## Not yet wired

- **Asset slot 2** (`{appearance}_asset_2.png`) — reserved for empty-state decor; `resolveAppearanceAsset(..., "empty")` exists but empty state UI does not render it yet.
- **Sidebar decor** — `resolveAppearanceAsset(..., "sidebar")` exists; no component uses it yet.
