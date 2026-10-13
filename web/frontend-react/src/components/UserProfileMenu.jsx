import { useEffect, useRef, useState } from "react";
import { tr } from "../i18n/strings.js";
import { SettingsMenuContent } from "./SettingsMenuContent.jsx";

function profileInitial(name) {
  const n = (name || "D").trim();
  return (n[0] || "D").toUpperCase();
}

/** One line describing how this tab talks to OpenAI ("key", "demo", "server-mock", "none"). */
function accessLabel(uiSettings, access) {
  if (access.mode === "key") return `${tr(uiSettings, "accessKey")} · ${access.maskedKey}`;
  if (access.mode === "demo") return tr(uiSettings, "accessDemo");
  if (access.mode === "server-mock") return tr(uiSettings, "accessServerMock");
  return tr(uiSettings, "accessNone");
}

function AccessButton({ t, onClick, children, primary = false }) {
  return (
    <button
      type="button"
      onClick={onClick}
      style={{
        flex: "1 1 auto",
        padding: "6px 10px",
        borderRadius: 8,
        border: `1px solid ${primary ? t.accent : t.border1}`,
        background: primary ? t.accentDim : "transparent",
        color: primary ? t.text1 : t.text2,
        fontSize: 12,
        fontWeight: 600,
        fontFamily: "inherit",
        cursor: "pointer",
        whiteSpace: "nowrap",
      }}
    >
      {children}
    </button>
  );
}

function AccessSection({ t, uiSettings, access, rtl, onEnterKey, onStartDemo, onSignOut }) {
  const dotColor =
    access.mode === "key" ? t.accent : access.mode === "none" ? t.err.color : t.text3;
  return (
    <div
      style={{
        marginBottom: 12,
        paddingBottom: 12,
        borderBottom: `1px solid ${t.border1}`,
        textAlign: rtl ? "right" : "left",
      }}
    >
      <div style={{ fontSize: 12, fontWeight: 600, color: t.text1, marginBottom: 6 }}>
        {tr(uiSettings, "accessTitle")}
      </div>
      <div
        style={{
          display: "flex",
          alignItems: "center",
          gap: 8,
          fontSize: 12,
          color: t.text2,
          flexDirection: rtl ? "row-reverse" : "row",
        }}
      >
        <span
          aria-hidden
          style={{ width: 8, height: 8, borderRadius: "50%", background: dotColor, flexShrink: 0 }}
        />
        <span style={{ fontFamily: access.mode === "key" ? "Consolas, monospace" : "inherit" }}>
          {accessLabel(uiSettings, access)}
        </span>
      </div>
      {access.mode === "demo" ? (
        <div style={{ fontSize: 11, color: t.text3, marginTop: 4 }}>
          {tr(uiSettings, "accessDemoHint")}
        </div>
      ) : null}
      {access.mode !== "server-mock" ? (
        <div
          style={{
            display: "flex",
            flexWrap: "wrap",
            gap: 6,
            marginTop: 10,
            flexDirection: rtl ? "row-reverse" : "row",
          }}
        >
          <AccessButton t={t} primary onClick={onEnterKey}>
            {tr(uiSettings, access.mode === "key" ? "accessChangeKey" : "accessEnterKey")}
          </AccessButton>
          {access.mode !== "demo" ? (
            <AccessButton t={t} onClick={onStartDemo}>
              {tr(uiSettings, "accessUseDemo")}
            </AccessButton>
          ) : null}
          {access.mode === "key" || access.mode === "demo" ? (
            <AccessButton t={t} onClick={onSignOut}>
              {tr(uiSettings, access.mode === "key" ? "accessRemoveKey" : "accessEndDemo")}
            </AccessButton>
          ) : null}
        </div>
      ) : null}
    </div>
  );
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
  access = { mode: "none", maskedKey: "" },
  onEnterKey,
  onStartDemo,
  onSignOut,
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
          <AccessSection
            t={t}
            uiSettings={uiSettings}
            access={access}
            rtl={rtl}
            onEnterKey={() => {
              setOpen(false);
              onEnterKey?.();
            }}
            onStartDemo={() => {
              setOpen(false);
              onStartDemo?.();
            }}
            onSignOut={() => {
              setOpen(false);
              onSignOut?.();
            }}
          />
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
            {access.mode === "none" ? tr(uiSettings, "profileRole") : accessLabel(uiSettings, access)}
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
