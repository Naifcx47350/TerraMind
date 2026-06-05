import { useState } from "react";

function SegmentedControl({ value, options, onChange, t }) {
  return (
    <div
      style={{
        display: "flex",
        gap: 4,
        padding: 3,
        background: t.bgInput,
        border: `1px solid ${t.border1}`,
        borderRadius: 8,
      }}
    >
      {options.map((opt) => {
        const active = value === opt.value;
        return (
          <button
            key={opt.value}
            type="button"
            onClick={() => onChange(opt.value)}
            style={{
              flex: 1,
              padding: "6px 8px",
              fontSize: 12,
              fontFamily: "inherit",
              fontWeight: active ? 600 : 400,
              color: active ? t.accent : t.text3,
              background: active ? t.bgCard : "transparent",
              border: active ? `1px solid ${t.border1}` : "1px solid transparent",
              borderRadius: 6,
              cursor: "pointer",
              transition: "all .15s",
            }}
          >
            {opt.label}
          </button>
        );
      })}
    </div>
  );
}

function CheckRow({ checked, onChange, label, t }) {
  return (
    <label
      style={{
        display: "flex",
        alignItems: "center",
        gap: 8,
        fontSize: 13,
        color: t.text3,
        cursor: "pointer",
        paddingLeft: 2,
        marginBottom: 10,
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

export function SettingsPanel({
  t,
  uiSettings,
  onChange,
  dark,
  onToggleDark,
}) {
  const [open, setOpen] = useState(true);

  const patch = (key, val) => onChange({ ...uiSettings, [key]: val });

  return (
    <div style={{ marginTop: 4 }}>
      <button
        type="button"
        onClick={() => setOpen((o) => !o)}
        style={{
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          width: "100%",
          background: "transparent",
          border: "none",
          cursor: "pointer",
          padding: "6px 2px",
          fontFamily: "inherit",
          color: t.text3,
          fontSize: 11,
          letterSpacing: "0.1em",
          textTransform: "uppercase",
          marginBottom: open ? 8 : 0,
        }}
      >
        Settings
        <span style={{ fontSize: 10, color: t.text4 }}>{open ? "▲" : "▼"}</span>
      </button>

      {open && (
        <div style={{ paddingBottom: 4 }}>
          <div
            style={{
              fontSize: 12,
              color: t.text3,
              marginBottom: 6,
            }}
          >
            Appearance
          </div>
          <SegmentedControl
            value={uiSettings.appearance}
            options={[
              { value: "classic", label: "Classic" },
              { value: "field", label: "Field" },
            ]}
            onChange={(v) => patch("appearance", v)}
            t={t}
          />

          <div style={{ height: 12 }} />

          <CheckRow
            checked={uiSettings.developerLabels}
            onChange={(v) => patch("developerLabels", v)}
            label="Developer labels"
            t={t}
          />
          <CheckRow
            checked={uiSettings.showSources}
            onChange={(v) => patch("showSources", v)}
            label="Show sources"
            t={t}
          />
          <CheckRow
            checked={uiSettings.showConfidence}
            onChange={(v) => patch("showConfidence", v)}
            label="Show confidence"
            t={t}
          />

          <button
            type="button"
            onClick={onToggleDark}
            style={{
              display: "flex",
              alignItems: "center",
              gap: 8,
              width: "100%",
              background: "transparent",
              border: `1px solid ${t.border1}`,
              borderRadius: 8,
              color: t.text3,
              fontFamily: "inherit",
              fontSize: 13,
              padding: "8px 12px",
              cursor: "pointer",
              transition: "background .15s",
              marginTop: 4,
            }}
            onMouseEnter={(e) => (e.currentTarget.style.background = t.bgHover)}
            onMouseLeave={(e) =>
              (e.currentTarget.style.background = "transparent")
            }
          >
            {dark ? "☀" : "☾"} {dark ? "Light mode" : "Dark mode"}
          </button>
        </div>
      )}
    </div>
  );
}
