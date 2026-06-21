import { useEffect, useRef, useState } from "react";
import { tr } from "../i18n/strings.js";
import { SettingsMenuContent } from "./SettingsMenuContent.jsx";

function profileInitial(name) {
  const n = (name || "D").trim();
  return (n[0] || "D").toUpperCase();
}

export function UserProfileMenu({
  t,
  uiSettings,
  onChange,
  dark,
  onToggleDark,
  rtl,
  stylized = false,
  profileDecorUrl,
  profileDecorStyle,
}) {
  const [open, setOpen] = useState(false);
  const wrapRef = useRef(null);

  useEffect(() => {
    if (!open) return;
    const close = (e) => {
      if (wrapRef.current && !wrapRef.current.contains(e.target)) setOpen(false);
    };
    document.addEventListener("mousedown", close);
    return () => document.removeEventListener("mousedown", close);
  }, [open]);

  const name =
    uiSettings.profileName?.trim() ||
    tr(uiSettings, "profileDefaultName");

  const showProfileDecor = stylized && profileDecorUrl;

  return (
    <div
      ref={wrapRef}
      style={{
        position: "relative",
      }}
    >
      {open && (
        <div
          className="tm-profile-menu"
          style={{
            position: "absolute",
            bottom: "calc(100% + 8px)",
            left: rtl ? undefined : 0,
            right: rtl ? 0 : undefined,
            width: "100%",
            minWidth: 240,
            background: t.bgCard,
            border: `1px solid ${t.border1}`,
            borderRadius: 12,
            boxShadow: `0 8px 28px rgba(0,0,0,${dark ? 0.45 : 0.12})`,
            padding: "12px 12px 8px",
            zIndex: 60,
            animation: "tm-scale-in .2s cubic-bezier(.22,1,.36,1) both",
            transformOrigin: rtl ? "bottom right" : "bottom left",
          }}
        >
          <div
            style={{
              fontSize: 12,
              fontWeight: 600,
              color: t.text1,
              marginBottom: 8,
              textAlign: rtl ? "right" : "left",
            }}
          >
            {tr(uiSettings, "settings")}
          </div>
          <SettingsMenuContent
            t={t}
            uiSettings={uiSettings}
            onChange={onChange}
            dark={dark}
            onToggleDark={onToggleDark}
            rtl={rtl}
          />
        </div>
      )}

      <button
        type="button"
        onClick={() => setOpen((o) => !o)}
        aria-expanded={open}
        aria-haspopup="dialog"
        style={{
          display: "flex",
          alignItems: "center",
          gap: 10,
          width: "100%",
          padding: "8px 6px",
          background: open ? t.bgHover : "transparent",
          border: "none",
          borderRadius: 10,
          cursor: "pointer",
          fontFamily: "inherit",
          textAlign: rtl ? "right" : "left",
          transition: "background .15s",
          flexDirection: rtl ? "row-reverse" : "row",
        }}
        onMouseEnter={(e) => {
          if (!open) e.currentTarget.style.background = t.bgHover;
        }}
        onMouseLeave={(e) => {
          if (!open) e.currentTarget.style.background = "transparent";
        }}
      >
        <div className="tm-profile-avatar-wrap">
          <div
            className="tm-profile-avatar"
            style={{
              width: 32,
              height: 32,
              borderRadius: "50%",
              background: t.bgActive,
              border: `1px solid ${t.border1}`,
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              flexShrink: 0,
              fontSize: 14,
              fontWeight: 700,
              color: t.text1,
            }}
          >
            {profileInitial(name)}
          </div>
          {showProfileDecor ? (
            <img
              src={profileDecorUrl}
              alt=""
              aria-hidden
              className="tm-profile-decor tm-decor-img tm-decor-fixed"
              style={profileDecorStyle}
            />
          ) : null}
        </div>
        <div style={{ flex: 1, minWidth: 0 }}>
          <div
            style={{
              fontSize: 13,
              fontWeight: 600,
              color: t.text1,
              whiteSpace: "nowrap",
              overflow: "hidden",
              textOverflow: "ellipsis",
            }}
          >
            {name}
          </div>
          <div
            style={{
              fontSize: 11,
              color: t.text3,
              whiteSpace: "nowrap",
              overflow: "hidden",
              textOverflow: "ellipsis",
            }}
          >
            {tr(uiSettings, "profileRole")}
          </div>
        </div>
        <svg
          width="16"
          height="16"
          viewBox="0 0 24 24"
          fill="none"
          stroke={t.text4}
          strokeWidth="2"
          strokeLinecap="round"
          strokeLinejoin="round"
          style={{
            flexShrink: 0,
            transform: open ? "rotate(180deg)" : "rotate(0deg)",
            transition: "transform .2s ease",
          }}
          aria-hidden
        >
          <polyline points="6 9 12 15 18 9" />
        </svg>
      </button>
    </div>
  );
}
