import { useState } from "react";
import { APPEARANCE_OPTIONS } from "../theme/index.js";
import { tr } from "../i18n/strings.js";
import { getDecorTuningForAppearance } from "../settings/uiSettings.js";
function CheckRow({ checked, onChange, label, t, rtl }) {
  return (
    <label
      style={{
        display: "flex",
        alignItems: "center",
        gap: 8,
        fontSize: 13,
        color: t.text2,
        cursor: "pointer",
        paddingLeft: rtl ? 0 : 2,
        paddingRight: rtl ? 2 : 0,
        marginBottom: 10,
        flexDirection: rtl ? "row-reverse" : "row",
      }}
    >
      <input
        type="checkbox"
        checked={checked}
        onChange={(e) => onChange(e.target.checked)}
        style={{ accentColor: t.accent, width: 14, height: 14 }}
      />
      {label}
    </label>
  );
}

function ThemeSwatches({ value, onChange, uiSettings, t }) {
  return (
    <div
      style={{
        display: "grid",
        gridTemplateColumns: "repeat(5, 1fr)",
        gap: 6,
        marginBottom: 12,
      }}
    >
      {APPEARANCE_OPTIONS.map((opt) => {
        const active = value === opt.id;
        return (
          <button
            key={opt.id}
            type="button"
            title={tr(uiSettings, `themes.${opt.id}`)}
            onClick={() => onChange(opt.id)}
            style={{
              display: "flex",
              flexDirection: "column",
              alignItems: "center",
              gap: 4,
              padding: "6px 2px",
              background: active ? t.accentDim : "transparent",
              border: active
                ? `2px solid ${t.accent}`
                : `1px solid ${t.border1}`,
              borderRadius: 8,
              cursor: "pointer",
              fontFamily: "inherit",
            }}
          >
            <span
              style={{
                width: 22,
                height: 22,
                borderRadius: "50%",
                background: opt.swatch,
                border: `1px solid ${t.border1}`,
              }}
            />
            <span
              style={{
                fontSize: 9,
                color: active ? t.accent : t.text3,
                lineHeight: 1.2,
                textAlign: "center",
              }}
            >
              {tr(uiSettings, `themes.${opt.id}`)}
            </span>
          </button>
        );
      })}
    </div>
  );
}

function LayoutModeToggle({ value, onChange, uiSettings, t, rtl }) {
  const stylized = !!value;
  return (
    <div style={{ marginBottom: 4 }}>
      <div
        style={{
          fontSize: 10,
          color: t.text3,
          letterSpacing: "0.05em",
          textTransform: "uppercase",
          marginBottom: 6,
          textAlign: rtl ? "right" : "left",
        }}
      >
        {tr(uiSettings, "layoutMode")}
      </div>
      <div className="tm-layout-toggle" role="group" aria-label={tr(uiSettings, "layoutMode")}>
        <button
          type="button"
          className={`tm-layout-toggle-btn${stylized ? " tm-layout-toggle-btn--active" : ""}`}
          onClick={() => onChange(true)}
          aria-pressed={stylized}
          style={{ color: stylized ? t.accent : t.text3 }}
        >
          <span className="tm-layout-toggle-icon" aria-hidden>
            ✦
          </span>
          <span className="tm-layout-toggle-label">
            {tr(uiSettings, "layoutStylized")}
          </span>
        </button>
        <button
          type="button"
          className={`tm-layout-toggle-btn${!stylized ? " tm-layout-toggle-btn--active" : ""}`}
          onClick={() => onChange(false)}
          aria-pressed={!stylized}
          style={{ color: !stylized ? t.text1 : t.text3 }}
        >
          <span className="tm-layout-toggle-icon" aria-hidden>
            ◻
          </span>
          <span className="tm-layout-toggle-label">
            {tr(uiSettings, "layoutSimple")}
          </span>
        </button>
      </div>
    </div>
  );
}

function AppearanceLayoutSection({
  uiSettings,
  onChange,
  t,
  rtl,
  patch,
}) {
  const stylized = uiSettings.stylizedLayout !== false;
  return (
    <div style={{ marginBottom: 14 }}>
      <LayoutModeToggle
        value={stylized}
        onChange={(v) => patch("stylizedLayout", v)}
        uiSettings={uiSettings}
        t={t}
        rtl={rtl}
      />
      {stylized ? (
        <AdvancedDecorPanel
          uiSettings={uiSettings}
          onChange={onChange}
          t={t}
          rtl={rtl}
        />
      ) : null}
      <div
        className="tm-layout-toggle-hint"
        style={{ textAlign: rtl ? "right" : "center", marginTop: stylized ? 6 : 0 }}
      >
        {stylized
          ? tr(uiSettings, "layoutStylizedHint")
          : tr(uiSettings, "layoutSimpleHint")}
      </div>
    </div>
  );
}

function AdvancedDecorPanel({ uiSettings, onChange, t, rtl }) {
  const [open, setOpen] = useState(false);
  const appearance = uiSettings.appearance;
  const tuning = getDecorTuningForAppearance(uiSettings, appearance);
  const byAppearance = uiSettings.decorTuning ?? {};

  const patchDecor = (role, key, val) => {
    onChange({
      ...uiSettings,
      decorTuning: {
        ...byAppearance,
        [appearance]: {
          ...tuning,
          [role]: { ...tuning[role], [key]: val },
        },
      },
    });
  };

  const row = (role, labelKey) => (
    <div key={role} style={{ marginBottom: 12 }}>
      <div
        style={{
          fontSize: 11,
          fontWeight: 600,
          color: t.text2,
          marginBottom: 6,
          textAlign: rtl ? "right" : "left",
        }}
      >
        {tr(uiSettings, labelKey)}
      </div>
      <label style={{ display: "block", fontSize: 10, color: t.text3, marginBottom: 4 }}>
        {tr(uiSettings, "decorSlot")}: {tuning[role]?.slot ?? 0}
        <input
          type="range"
          min={0}
          max={3}
          step={1}
          value={tuning[role]?.slot ?? 0}
          onChange={(e) => patchDecor(role, "slot", Number(e.target.value))}
          style={{ width: "100%", accentColor: t.accent, marginTop: 4 }}
        />
      </label>
      <label style={{ display: "block", fontSize: 10, color: t.text3, marginBottom: 4 }}>
        {tr(uiSettings, "decorOpacity")}: {(tuning[role]?.opacity ?? 1).toFixed(2)}
        <input
          type="range"
          min={0}
          max={1}
          step={0.05}
          value={tuning[role]?.opacity ?? 1}
          onChange={(e) => patchDecor(role, "opacity", Number(e.target.value))}
          style={{ width: "100%", accentColor: t.accent, marginTop: 4 }}
        />
      </label>
      <label style={{ display: "block", fontSize: 10, color: t.text3 }}>
        {tr(uiSettings, "decorRotation")}: {tuning[role]?.rotation ?? 0}°
        <input
          type="range"
          min={-180}
          max={180}
          step={1}
          value={tuning[role]?.rotation ?? 0}
          onChange={(e) => patchDecor(role, "rotation", Number(e.target.value))}
          style={{ width: "100%", accentColor: t.accent, marginTop: 4 }}
        />
      </label>
    </div>
  );

  return (
    <div style={{ marginBottom: 0 }}>
      <button
        type="button"
        className="tm-advanced-toggle"
        onClick={() => setOpen((o) => !o)}
        aria-expanded={open}
        style={{
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          width: "100%",
          padding: "8px 10px",
          borderRadius: 10,
          border: `1px solid ${t.border1}`,
          background: t.bgInput,
          color: t.text2,
          fontFamily: "inherit",
          fontSize: 12,
          fontWeight: 600,
          cursor: "pointer",
          flexDirection: rtl ? "row-reverse" : "row",
        }}
      >
        <span>{tr(uiSettings, "advancedOptions")}</span>
        <span
          aria-hidden
          style={{
            color: t.text3,
            transform: open ? "rotate(180deg)" : "rotate(0deg)",
            transition: "transform .2s ease",
          }}
        >
          ▾
        </span>
      </button>
      {open ? (
        <div
          className="tm-advanced-panel"
          style={{
            marginTop: 6,
            padding: "10px 10px 2px",
            borderRadius: 10,
            border: `1px solid ${t.border1}`,
            background: t.bgInput,
          }}
        >
          {row("profile", "decorProfile")}
          {row("composer", "decorComposer")}
        </div>
      ) : null}
    </div>
  );
}

export function SettingsMenuContent({
  t,
  uiSettings,
  onChange,
  dark,
  onToggleDark,
  rtl,
}) {
  const patch = (key, val) => onChange({ ...uiSettings, [key]: val });

  return (
    <div style={{ padding: "4px 2px 8px" }}>
      <div
        style={{
          fontSize: 11,
          color: t.text3,
          letterSpacing: "0.06em",
          textTransform: "uppercase",
          marginBottom: 8,
          textAlign: rtl ? "right" : "left",
        }}
      >
        {tr(uiSettings, "appearance")}
      </div>
      <ThemeSwatches
        value={uiSettings.appearance}
        onChange={(v) => patch("appearance", v)}
        uiSettings={uiSettings}
        t={t}
      />

      <AppearanceLayoutSection
        uiSettings={uiSettings}
        onChange={onChange}
        t={t}
        rtl={rtl}
        patch={patch}
      />

      <div
        style={{
          fontSize: 11,
          color: t.text3,
          letterSpacing: "0.06em",
          textTransform: "uppercase",
          marginBottom: 8,
          marginTop: 4,
          textAlign: rtl ? "right" : "left",
        }}
      >
        {tr(uiSettings, "language")}
      </div>
      <div
        style={{
          display: "flex",
          gap: 4,
          padding: 3,
          background: t.bgInput,
          border: `1px solid ${t.border1}`,
          borderRadius: 8,
          marginBottom: 12,
        }}
      >
        {[
          { value: "en", label: tr(uiSettings, "langEn") },
          { value: "ar", label: tr(uiSettings, "langAr") },
        ].map((opt) => {
          const active = uiSettings.language === opt.value;
          return (
            <button
              key={opt.value}
              type="button"
              onClick={() => patch("language", opt.value)}
              style={{
                flex: 1,
                padding: "6px 8px",
                fontSize: 12,
                fontFamily: "inherit",
                fontWeight: active ? 600 : 400,
                color: active ? t.accent : t.text3,
                background: active ? t.bgCard : "transparent",
                border: active
                  ? `1px solid ${t.border1}`
                  : "1px solid transparent",
                borderRadius: 6,
                cursor: "pointer",
              }}
            >
              {opt.label}
            </button>
          );
        })}
      </div>

      <CheckRow
        checked={uiSettings.developerLabels}
        onChange={(v) => patch("developerLabels", v)}
        label={tr(uiSettings, "developerLabels")}
        t={t}
        rtl={rtl}
      />
      <CheckRow
        checked={uiSettings.showSources}
        onChange={(v) => patch("showSources", v)}
        label={tr(uiSettings, "showSources")}
        t={t}
        rtl={rtl}
      />
      <CheckRow
        checked={uiSettings.showConfidence}
        onChange={(v) => patch("showConfidence", v)}
        label={tr(uiSettings, "showConfidence")}
        t={t}
        rtl={rtl}
      />

      <button
        type="button"
        onClick={onToggleDark}
        style={{
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          gap: 8,
          width: "100%",
          background: t.bgInput,
          border: `1px solid ${t.border1}`,
          borderRadius: 8,
          color: t.text2,
          fontFamily: "inherit",
          fontSize: 13,
          padding: "9px 12px",
          cursor: "pointer",
          transition: "background .15s",
          marginTop: 4,
        }}
        onMouseEnter={(e) => (e.currentTarget.style.background = t.bgHover)}
        onMouseLeave={(e) =>
          (e.currentTarget.style.background = t.bgInput)
        }
      >
        {dark ? "☀" : "☾"}{" "}
        {dark
          ? tr(uiSettings, "lightMode")
          : tr(uiSettings, "darkMode")}
      </button>
    </div>
  );
}
