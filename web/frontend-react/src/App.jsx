import { useState, useRef, useEffect } from "react";
import { MarkdownMessage } from "./MarkdownMessage";
import { resolveTheme } from "./theme/index.js";
import { loadUiSettings, saveUiSettings, getDecorTuningForAppearance } from "./settings/uiSettings.js";
import {
  getModelDisplay,
  getRoutedDisplay,
  getModelDescription,
} from "./settings/modelLabels.js";
import { tr, isRtlUi } from "./i18n/strings.js";
import { UserProfileMenu } from "./components/UserProfileMenu.jsx";
import { NewChatButton } from "./components/NewChatButton.jsx";
import { SourceList } from "./components/SourceList.jsx";
import { ConfidenceBadge } from "./components/ConfidenceBadge.jsx";
import { AdvisoryPanels, shouldUseAdvisoryPanels } from "./components/AdvisoryPanels.jsx";
import { RoutePill } from "./components/RoutePill.jsx";
import { BotAvatar } from "./components/BotAvatar.jsx";
import { TerraLogo } from "./components/TerraLogo.jsx";
import { SidebarWelcomeCard } from "./components/SidebarWelcomeCard.jsx";
import {
  resolveAppearanceAsset,
  resolveThemeBackground,
  decorImageStyle,
} from "./theme/backgroundAssets.js";
import { DEFAULT_BACKGROUND_LAYOUT } from "./theme/decorDefaults/index.js";

const API = "/api";

const ADVISORY_MODEL = {
  id: "advisory",
  name: "Advisory (General + Product)",
  description: "IPM guidance from public refs, then catalog products",
};

const ADVISORY_UNLOCK_KEY = "terramind_advisory_unlocked_v1";
const LOGO_CLICKS_NEEDED = 7;
const LOGO_CLICK_RESET_MS = 2500;

const DEFAULT_MODELS = [
  {
    id: "auto_rag",
    name: "Auto (recommended)",
    description:
      "Picks Product Catalog or Agriculture Knowledge RAG from your question",
  },
  {
    id: "general_rag",
    name: "Agriculture Knowledge RAG",
    description:
      "Public refs: GAP, soil health, rotation, IPM — not product catalog",
  },
  {
    id: "product_rag",
    name: "Product Catalog RAG",
    description: "Client Excel product sheets",
  },
  {
    id: "base_llm",
    name: "Base LLM",
    description: "OpenAI only — no retrieval",
  },
];

function withAdvisoryOption(modelList, unlocked) {
  if (!unlocked) return modelList.filter((m) => m.id !== "advisory");
  if (modelList.some((m) => m.id === "advisory")) return modelList;
  return [...modelList, ADVISORY_MODEL];
}

function resolveRequestModel(selectedModel, advisoryUnlocked) {
  if (selectedModel === "advisory") {
    return advisoryUnlocked ? "advisory" : "auto_rag";
  }
  return selectedModel || "auto_rag";
}

function hexToRgb(hex) {
  const h = String(hex || "").replace("#", "");
  if (h.length !== 3 && h.length !== 6) return "16,163,127";
  const full =
    h.length === 3
      ? h
          .split("")
          .map((c) => c + c)
          .join("")
      : h;
  const n = parseInt(full, 16);
  return `${(n >> 16) & 255},${(n >> 8) & 255},${n & 255}`;
}

function textSizeTokens(textScale) {
  const rawScale = Number(textScale);
  const scale = Math.min(
    6,
    Math.max(0, Number.isFinite(rawScale) ? rawScale : 2),
  );
  const sizes = [
    { chat: 12, user: 12, meta: 10, composer: 12 },
    { chat: 13, user: 13, meta: 11, composer: 13 },
    { chat: 14, user: 14, meta: 12, composer: 14 },
    { chat: 16, user: 15, meta: 13, composer: 16 },
    { chat: 18, user: 17, meta: 14, composer: 17 },
    { chat: 20, user: 19, meta: 15, composer: 19 },
    { chat: 22, user: 21, meta: 16, composer: 21 },
  ];
  return sizes[scale] || sizes[2];
}

/** Same three backends as core.models.COMPARE_MODEL_IDS (Auto excluded). */
const COMPARE_MODEL_IDS = ["product_rag", "general_rag", "base_llm"];

function compareModelList(modelList, developerLabels = false, language = "en") {
  const byId = Object.fromEntries(modelList.map((m) => [m.id, m]));
  return COMPARE_MODEL_IDS.map((id) => {
    const fromApi = byId[id];
    const labels = getModelDisplay(id, { developerLabels, language });
    return {
      id,
      name: labels.friendly,
      technical: labels.technical,
      description: getModelDescription(id, language, fromApi?.description || ""),
    };
  });
}

const AUTO_ROUTE_HINT_MS = 10000;

function AutoRouteHint({ label, technical, reason, t, fading, developerLabels, rtl, usingPrefix }) {
  if (!label) return null;
  return (
    <div
      className="tm-auto-route-hint"
      title={reason || technical || ""}
      style={{
        color: t.text3,
        opacity: fading ? 0 : 1,
        transition: "opacity 0.6s ease",
        pointerEvents: "none",
        direction: rtl ? "rtl" : "ltr",
        unicodeBidi: "isolate",
        textAlign: rtl ? "left" : "right",
      }}
    >
      <span className="tm-auto-route-hint-main">
        <span>{usingPrefix} </span>
        <bdi style={{ fontWeight: 600, unicodeBidi: "isolate" }} dir="auto">
          {label}
        </bdi>
      </span>
      {developerLabels && technical && (
        <div className="tm-auto-route-hint-tech" style={{ color: t.text3 }}>
          {technical}
        </div>
      )}
    </div>
  );
}

function ComparePanels({
  msg,
  models,
  t,
  uiSettings,
  isAr,
  appearance,
}) {
  const compareModels = compareModelList(
    models,
    uiSettings.developerLabels,
    uiSettings.language,
  );
  const showSrc = uiSettings.showSources;
  const showScores = uiSettings.showConfidence;
  const panels =
    msg.panels?.length > 0
      ? msg.panels
      : compareModels.map((m) => ({
          modelId: m.id,
          modelName: m.name,
          answer: "",
          sources: [],
          latency: 0,
          loading: true,
        }));

  return (
    <div style={{ marginBottom: 24 }}>
      <div
        style={{
          fontSize: 11,
          color: t.text3,
          letterSpacing: "0.08em",
          textTransform: "uppercase",
          marginBottom: 10,
        }}
      >
        Compare · {msg.time}
        {msg.latency ? ` · ${msg.latency}ms total` : ""}
      </div>
      <div
        style={{
          display: "grid",
          gridTemplateColumns: "repeat(3, minmax(0, 1fr))",
          gap: 12,
          alignItems: "stretch",
        }}
      >
        {panels.map((panel) => {
          const ar = isAr(panel.answer);
          return (
            <div
              key={panel.modelId}
              style={{
                display: "flex",
                flexDirection: "column",
                minHeight: 160,
                background: t.bgCard,
                border: `1px solid ${t.border1}`,
                borderRadius: 12,
                overflow: "hidden",
              }}
            >
              <div
                style={{
                  padding: "10px 12px",
                  borderBottom: `1px solid ${t.border1}`,
                  background: t.bgSide,
                  flexShrink: 0,
                }}
              >
                <div
                  style={{
                    fontSize: 13,
                    fontWeight: 600,
                    color: t.text1,
                    lineHeight: 1.3,
                  }}
                >
                  {panel.modelName}
                </div>
                {compareModels.find((m) => m.id === panel.modelId)?.technical && (
                  <div style={{ fontSize: 10, color: t.text3, marginTop: 2, lineHeight: 1.3 }}>
                    {compareModels.find((m) => m.id === panel.modelId).technical}
                  </div>
                )}
                {panel.latency != null && !panel.loading && (
                  <div style={{ fontSize: 11, color: t.text3, marginTop: 2 }}>
                    {panel.latency}ms
                  </div>
                )}
              </div>
              <div
                style={{
                  flex: 1,
                  padding: "12px",
                  fontSize: "var(--tm-chat-font-size)",
                  color: panel.error ? t.err.color : t.text2,
                  lineHeight: 1.7,
                  wordBreak: "break-word",
                  direction: ar ? "rtl" : "ltr",
                  textAlign: ar ? "right" : "left",
                  overflowY: "auto",
                  maxHeight: 420,
                }}
              >
                {panel.loading ? (
                  <div style={{ display: "flex", gap: 4, paddingTop: 4 }}>
                    {[0, 1, 2].map((i) => (
                      <div
                        key={i}
                        style={{
                          width: 6,
                          height: 6,
                          borderRadius: "50%",
                          background: t.text4,
                          animation: `dot .9s ${i * 0.2}s ease-in-out infinite`,
                        }}
                      />
                    ))}
                  </div>
                ) : panel.error ? (
                  panel.error
                ) : panel.answer ? (
                  <MarkdownMessage
                    content={panel.answer}
                    theme={t}
                    dir={ar ? "rtl" : "ltr"}
                  />
                ) : (
                  "—"
                )}
                {showScores && !panel.loading && !panel.error && (
                  <ConfidenceBadge
                    confidence={panel.confidence}
                    retrievalScore={panel.retrieval_score}
                    retrievedChunks={panel.retrieved_chunks}
                    modelId={panel.modelId}
                    t={t}
                    ar={ar}
                    appearance={appearance}
                  />
                )}
              </div>
              {showSrc && panel.sources?.length > 0 && !panel.loading && (
                <div
                  style={{
                    padding: "8px 12px 12px",
                    borderTop: `1px solid ${t.border2}`,
                    flexShrink: 0,
                  }}
                >
                  <SourceList
                    sources={panel.sources}
                    t={t}
                    ar={ar}
                    appearance={appearance}
                  />
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}

function sanitize(str) {
  const d = document.createElement("div");
  d.textContent = str;
  return d.innerHTML;
}

const SESSIONS_STORAGE_KEY = "terramind_sessions_v1";
const OPENAI_KEY_SESSION = "terramind_openai_key_session_v1";
const SIDEBAR_WIDTH = 280;

function formatClockTime(language = "en") {
  return new Date().toLocaleTimeString(language === "ar" ? "ar" : "en-US", {
    hour: "2-digit",
    minute: "2-digit",
    hour12: false,
  });
}

function newSession() {
  return {
    id: Date.now(),
    name: "New conversation",
    messages: [],
    ts: formatClockTime("en"),
  };
}

function loadStoredSessions() {
  try {
    const raw = localStorage.getItem(SESSIONS_STORAGE_KEY);
    if (!raw) return null;
    const data = JSON.parse(raw);
    if (!Array.isArray(data.sessions) || data.sessions.length === 0)
      return null;
    return {
      sessions: data.sessions,
      activeId: data.activeId ?? data.sessions[0].id,
    };
  } catch {
    return null;
  }
}

function sessionsForStorage(sessions) {
  return sessions.map((s) => ({
    ...s,
    messages: s.messages.map((m) =>
      m.role === "user" ? { ...m, imgPreview: null } : m,
    ),
  }));
}

function sessionSearchableText(session) {
  const parts = [session.name || ""];
  for (const m of session.messages || []) {
    if (m.role === "user") parts.push(m.text || "");
    else if (m.role === "bot") parts.push(m.answer || "");
    else if (m.role === "error") parts.push(m.text || "");
    else if (m.role === "compare" && m.panels) {
      for (const p of m.panels) {
        parts.push(p.modelName || "", p.answer || "", p.error || "");
      }
    }
  }
  return parts.join(" ").toLowerCase();
}

function sessionMatchesSearch(session, query) {
  const q = query.trim().toLowerCase();
  if (!q) return true;
  return sessionSearchableText(session).includes(q);
}

function fileToBase64(f) {
  return new Promise((r, e) => {
    const x = new FileReader();
    x.onload = () => r(x.result.split(",")[1]);
    x.onerror = e;
    x.readAsDataURL(f);
  });
}

/* Icons */
const I = {
  sidebar: () => (
    <svg
      width="18"
      height="18"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.8"
      strokeLinecap="round"
      strokeLinejoin="round"
    >
      <rect x="3" y="3" width="18" height="18" rx="2" />
      <line x1="9" y1="3" x2="9" y2="21" />
    </svg>
  ),
  plus: () => (
    <svg
      width="16"
      height="16"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.8"
      strokeLinecap="round"
      strokeLinejoin="round"
    >
      <path d="M12 5v14M5 12h14" />
    </svg>
  ),
  search: ({ c = "currentColor" }) => (
    <svg
      width="14"
      height="14"
      viewBox="0 0 24 24"
      fill="none"
      stroke={c}
      strokeWidth="1.8"
      strokeLinecap="round"
      strokeLinejoin="round"
    >
      <circle cx="11" cy="11" r="8" />
      <line x1="21" y1="21" x2="16.65" y2="16.65" />
    </svg>
  ),
  sun: () => (
    <svg
      width="15"
      height="15"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.8"
      strokeLinecap="round"
      strokeLinejoin="round"
    >
      <circle cx="12" cy="12" r="5" />
      <line x1="12" y1="1" x2="12" y2="3" />
      <line x1="12" y1="21" x2="12" y2="23" />
      <line x1="4.22" y1="4.22" x2="5.64" y2="5.64" />
      <line x1="18.36" y1="18.36" x2="19.78" y2="19.78" />
      <line x1="1" y1="12" x2="3" y2="12" />
      <line x1="21" y1="12" x2="23" y2="12" />
      <line x1="4.22" y1="19.78" x2="5.64" y2="18.36" />
      <line x1="18.36" y1="5.64" x2="19.78" y2="4.22" />
    </svg>
  ),
  mic: ({ c = "currentColor" } = {}) => (
    <svg
      width="17"
      height="17"
      viewBox="0 0 24 24"
      fill="none"
      stroke={c}
      strokeWidth="1.9"
      strokeLinecap="round"
      strokeLinejoin="round"
    >
      <path d="M12 3a3 3 0 0 0-3 3v6a3 3 0 0 0 6 0V6a3 3 0 0 0-3-3Z" />
      <path d="M19 10v2a7 7 0 0 1-14 0v-2" />
      <path d="M12 19v3" />
      <path d="M8 22h8" />
    </svg>
  ),
  check: ({ c = "currentColor" } = {}) => (
    <svg
      width="16"
      height="16"
      viewBox="0 0 24 24"
      fill="none"
      stroke={c}
      strokeWidth="2.2"
      strokeLinecap="round"
      strokeLinejoin="round"
    >
      <path d="M20 6 9 17l-5-5" />
    </svg>
  ),
  moon: () => (
    <svg
      width="15"
      height="15"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.8"
      strokeLinecap="round"
      strokeLinejoin="round"
    >
      <path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z" />
    </svg>
  ),
  send: ({ on, c }) => (
    <svg
      width="16"
      height="16"
      viewBox="0 0 24 24"
      fill={on ? c : "none"}
      stroke={c}
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
    >
      <line x1="22" y1="2" x2="11" y2="13" />
      <polygon points="22 2 15 22 11 13 2 9 22 2" />
    </svg>
  ),
  img: ({ c }) => (
    <svg
      width="16"
      height="16"
      viewBox="0 0 24 24"
      fill="none"
      stroke={c}
      strokeWidth="1.8"
      strokeLinecap="round"
      strokeLinejoin="round"
    >
      <rect x="3" y="3" width="18" height="18" rx="2" />
      <circle cx="8.5" cy="8.5" r="1.5" />
      <polyline points="21 15 16 10 5 21" />
    </svg>
  ),
  chat: ({ c }) => (
    <svg
      width="13"
      height="13"
      viewBox="0 0 24 24"
      fill="none"
      stroke={c}
      strokeWidth="1.8"
      strokeLinecap="round"
      strokeLinejoin="round"
    >
      <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z" />
    </svg>
  ),
  trash: ({ c }) => (
    <svg
      width="13"
      height="13"
      viewBox="0 0 24 24"
      fill="none"
      stroke={c}
      strokeWidth="1.8"
      strokeLinecap="round"
      strokeLinejoin="round"
    >
      <polyline points="3 6 5 6 21 6" />
      <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2" />
    </svg>
  ),
  chevron: ({ c }) => (
    <svg
      width="14"
      height="14"
      viewBox="0 0 24 24"
      fill="none"
      stroke={c}
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
    >
      <polyline points="6 9 12 15 18 9" />
    </svg>
  ),
  columns: ({ c }) => (
    <svg
      width="16"
      height="16"
      viewBox="0 0 24 24"
      fill="none"
      stroke={c}
      strokeWidth="1.8"
      strokeLinecap="round"
      strokeLinejoin="round"
    >
      <rect x="3" y="3" width="5" height="18" rx="1" />
      <rect x="10" y="3" width="5" height="18" rx="1" />
      <rect x="17" y="3" width="5" height="18" rx="1" />
    </svg>
  ),
};

async function consumeNdjsonStream(response, onEvent) {
  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";
  while (true) {
    const { done, value } = await reader.read();
    if (done) break;
    buffer += decoder.decode(value, { stream: true });
    const lines = buffer.split("\n");
    buffer = lines.pop() ?? "";
    for (const line of lines) {
      if (!line.trim()) continue;
      onEvent(JSON.parse(line));
    }
  }
  if (buffer.trim()) {
    onEvent(JSON.parse(buffer.trim()));
  }
}

function BootstrapOverlay({ t, logoFilter, logoGlow, logoTint }) {
  return (
    <div
      className="tm-bootstrap-overlay"
      style={{
        position: "fixed",
        inset: 0,
        zIndex: 10001,
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        justifyContent: "center",
        gap: 16,
        background: "rgba(0,0,0,0.72)",
        backdropFilter: "blur(6px)",
      }}
      aria-live="polite"
      aria-busy="true"
    >
      <TerraLogo
        size={40}
        logoFilter={logoFilter}
        logoGlow={logoGlow}
        logoTint={logoTint}
      />
      <div style={{ fontSize: 15, fontWeight: 600, color: t.text1 }}>
        Starting TerraMind…
      </div>
      <div style={{ fontSize: 13, color: t.text3 }}>
        Waiting for the Model API to finish loading.
      </div>
    </div>
  );
}

function ApiKeyGate({
  t,
  open,
  exiting,
  reason,
  value,
  onChange,
  onSubmit,
  submitting,
  error,
  logoFilter = "none",
  logoGlow,
  logoTint,
}) {
  const [privacyOpen, setPrivacyOpen] = useState(false);

  if (!open && !exiting) return null;

  const isReauth = reason === "reauth";
  const lead = isReauth
    ? "The key you entered earlier no longer works — it may have expired or been turned off in your OpenAI account. Enter a new key below to keep using TerraMind."
    : "TerraMind is your agriculture assistant for questions, document search, and crop photo analysis. To use it, paste your OpenAI API key below.";

  return (
    <div
      className={`tm-gate-backdrop${exiting ? " tm-gate-exiting" : ""}`}
      style={{
        position: "fixed",
        inset: 0,
        zIndex: 10000,
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        padding: 24,
        background: "rgba(0,0,0,0.78)",
        backdropFilter: "blur(8px)",
      }}
    >
      <div
        role="dialog"
        aria-labelledby="api-key-title"
        className="tm-gate-modal"
        style={{
          width: "min(100%, 440px)",
          background: `linear-gradient(165deg, ${t.bgCard} 0%, ${t.bgSide} 100%)`,
          border: `1px solid ${t.border1}`,
          borderRadius: 20,
          padding: "28px 28px 24px",
          boxShadow: `0 32px 64px rgba(0,0,0,${t.bg === "#0a0a0a" ? "0.5" : "0.14"}), 0 0 0 1px rgba(16,163,127,0.08)`,
        }}
      >
        <div
          className="tm-stagger-1"
          style={{ display: "flex", alignItems: "center", gap: 12, marginBottom: 18 }}
        >
          <div className="tm-gate-logo">
            <TerraLogo
              size={36}
              logoFilter={logoFilter}
              logoGlow={logoGlow}
              logoTint={logoTint}
            />
          </div>
          <div>
            <div
              id="api-key-title"
              style={{ fontSize: 18, fontWeight: 700, color: t.text1 }}
            >
              {isReauth ? "Please update your API key" : "Welcome to TerraMind"}
            </div>
            <div style={{ fontSize: 13, color: t.text3, marginTop: 4 }}>
              {isReauth
                ? "A new key is needed to continue."
                : "One quick step before you can start chatting."}
            </div>
          </div>
        </div>

        <p
          className="tm-stagger-2"
          style={{ fontSize: 13, color: t.text2, lineHeight: 1.65, marginBottom: 14 }}
        >
          {lead}
        </p>

        <div
          className="tm-stagger-3"
          style={{
            fontSize: 12,
            color: t.text3,
            lineHeight: 1.65,
            marginBottom: 18,
            padding: "10px 12px",
            borderRadius: 8,
            background: t.bgInput,
            border: `1px solid ${t.border1}`,
          }}
        >
          {isReauth ? (
            <>
              <div style={{ fontWeight: 600, color: t.text2, marginBottom: 4 }}>
                What happened?
              </div>
              <p style={{ margin: 0 }}>
                OpenAI did not accept your previous key. Create or copy a new one from your
                OpenAI account and paste it below.
              </p>
            </>
          ) : (
            <>
              <div style={{ fontWeight: 600, color: t.text2, marginBottom: 4 }}>
                Don&apos;t have a key yet?
              </div>
              <p style={{ margin: 0 }}>
                Sign in at{" "}
                <a
                  href="https://platform.openai.com/api-keys"
                  target="_blank"
                  rel="noopener noreferrer"
                  style={{ color: t.accent, textDecoration: "none" }}
                >
                  platform.openai.com
                </a>
                , create an API key, and paste it here. TerraMind uses it to connect to OpenAI
                on your behalf.
              </p>
            </>
          )}
        </div>

        <div
          className="tm-stagger-4"
          style={{
            marginBottom: 18,
            borderRadius: 10,
            background: t.accentDim,
            border: `1px solid ${t.accent}`,
            borderLeftWidth: 4,
            overflow: "hidden",
          }}
        >
          <button
            type="button"
            onClick={() => setPrivacyOpen((v) => !v)}
            aria-expanded={privacyOpen}
            style={{
              display: "flex",
              alignItems: "center",
              gap: 10,
              width: "100%",
              padding: "11px 14px",
              border: "none",
              background: "transparent",
              cursor: "pointer",
              textAlign: "left",
              color: t.text1,
            }}
          >
            <svg
              width="18"
              height="18"
              viewBox="0 0 24 24"
              fill="none"
              stroke={t.accent}
              strokeWidth="2"
              strokeLinecap="round"
              strokeLinejoin="round"
              style={{ flexShrink: 0 }}
              aria-hidden
            >
              <rect x="3" y="11" width="18" height="11" rx="2" ry="2" />
              <path d="M7 11V7a5 5 0 0 1 10 0v4" />
            </svg>
            <span style={{ flex: 1, fontSize: 13, fontWeight: 600 }}>
              Don&apos;t worry — your key is private
            </span>
            <svg
              width="16"
              height="16"
              viewBox="0 0 24 24"
              fill="none"
              stroke={t.text3}
              strokeWidth="2"
              strokeLinecap="round"
              strokeLinejoin="round"
              style={{
                flexShrink: 0,
                transform: privacyOpen ? "rotate(180deg)" : "rotate(0deg)",
                transition: "transform 0.25s cubic-bezier(.22,1,.36,1)",
              }}
              aria-hidden
            >
              <polyline points="6 9 12 15 18 9" />
            </svg>
          </button>
          <div
            className={`tm-privacy-collapse${privacyOpen ? " tm-privacy-open" : ""}`}
          >
            <div className="tm-privacy-inner">
              <div
                style={{
                  padding: "0 14px 12px 42px",
                  fontSize: 12,
                  color: t.text2,
                  lineHeight: 1.65,
                }}
              >
                Your API key is kept only in this browser tab while you use TerraMind. It is not
                saved to our servers, shared with other users, or written to files on your computer.
                Close this tab and it is cleared.
              </div>
            </div>
          </div>
        </div>

        <div className="tm-stagger-5">
        <label style={{ display: "block", fontSize: 12, color: t.text3, marginBottom: 6 }}>
          OpenAI API key
        </label>
        <input
          type="password"
          className="tm-gate-input"
          value={value}
          onChange={(e) => onChange(e.target.value)}
          placeholder="sk-…"
          autoComplete="off"
          spellCheck={false}
          style={{
            width: "100%",
            boxSizing: "border-box",
            padding: "10px 12px",
            borderRadius: 10,
            border: `1px solid ${error ? t.err.b : t.border1}`,
            background: t.bgInput,
            color: t.text1,
            fontFamily: "Consolas, monospace",
            fontSize: 13,
            marginBottom: error ? 8 : 16,
          }}
          onKeyDown={(e) => {
            if (e.key === "Enter") onSubmit();
          }}
        />
        {error && (
          <div
            style={{
              fontSize: 12,
              color: t.err.color,
              marginBottom: 12,
              lineHeight: 1.5,
              animation: "tm-slide-up 0.3s ease both",
            }}
          >
            {error}
          </div>
        )}
        <button
          type="button"
          className={`tm-btn-primary${submitting ? " tm-btn-loading" : ""}`}
          onClick={onSubmit}
          disabled={submitting || !value.trim()}
          style={{
            width: "100%",
            padding: "11px 16px",
            borderRadius: 10,
            border: "none",
            background: submitting ? t.text4 : t.accent,
            color: t.btnText,
            fontWeight: 600,
            fontSize: 14,
            cursor: submitting || !value.trim() ? "not-allowed" : "pointer",
            opacity: submitting || !value.trim() ? 0.7 : 1,
          }}
        >
          {submitting ? "Connecting" : isReauth ? "Update key and continue" : "Continue"}
        </button>
        </div>
      </div>
    </div>
  );
}

async function applyOpenAIKeyToServer(apiKey) {
  const r = await fetch(`${API}/config/openai-key`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ api_key: apiKey.trim() }),
  });
  const data = await r.json().catch(() => ({}));
  if (!r.ok) {
    const detail = data.detail;
    throw new Error(
      typeof detail === "string"
        ? detail
        : Array.isArray(detail)
          ? detail.map((x) => x.msg || x).join(", ")
          : `Server error ${r.status}`,
    );
  }
  return data;
}

function isOpenAIKeyError(error) {
  const msg = String(error?.message || error || "").toLowerCase();
  return (
    msg.includes("invalid_api_key") ||
    msg.includes("incorrect api key") ||
    (msg.includes("api key") && msg.includes("openai")) ||
    msg.includes("placeholder or masked")
  );
}

export default function App() {
  const stored = loadStoredSessions();
  const [dark, setDark] = useState(true);
  const [uiSettings, setUiSettings] = useState(() => loadUiSettings());
  const [sideOpen, setSideOpen] = useState(true);
  const [sessions, setSessions] = useState(
    () => stored?.sessions ?? [newSession()],
  );
  const [activeId, setActiveId] = useState(
    () => stored?.activeId ?? stored?.sessions?.[0]?.id ?? Date.now(),
  );
  const [dragOver, setDragOver] = useState(false);
  const [text, setText] = useState("");
  const [image, setImage] = useState(null);
  const [loading, setLoading] = useState(false);
  const [hover, setHover] = useState(null);
  const [models, setModels] = useState(DEFAULT_MODELS);
  const [selectedModel, setSelectedModel] = useState("auto_rag");
  const [advisoryUnlocked, setAdvisoryUnlocked] = useState(false);
  const [modelOpen, setModelOpen] = useState(false);
  const [autoRouteHint, setAutoRouteHint] = useState(null);
  const [autoRouteFading, setAutoRouteFading] = useState(false);
  const autoRouteTimerRef = useRef(null);
  const logoClickRef = useRef({ count: 0, lastAt: 0 });
  const [compareMode, setCompareMode] = useState(false);
  const [activeRequestSessionId, setActiveRequestSessionId] = useState(null);
  const [convSearch, setConvSearch] = useState("");
  const [voiceMenuOpen, setVoiceMenuOpen] = useState(false);
  const [voiceDevices, setVoiceDevices] = useState([]);
  const [selectedVoiceDeviceId, setSelectedVoiceDeviceId] = useState("");
  const [holdToRecord, setHoldToRecord] = useState(true);
  const [listening, setListening] = useState(false);
  const [voiceLevel, setVoiceLevel] = useState(0);
  const [voiceError, setVoiceError] = useState("");
  const [interimTranscript, setInterimTranscript] = useState("");
  const [apiKeyReady, setApiKeyReady] = useState(false);
  const [apiConfigLoading, setApiConfigLoading] = useState(true);
  const [showApiKeyGate, setShowApiKeyGate] = useState(false);
  const [apiKeyInput, setApiKeyInput] = useState("");
  const [apiKeyError, setApiKeyError] = useState("");
  const [apiKeySubmitting, setApiKeySubmitting] = useState(false);
  const [apiKeyGateReason, setApiKeyGateReason] = useState("initial");
  const [gateExiting, setGateExiting] = useState(false);
  const bottomRef = useRef(null);
  const fileRef = useRef(null);
  const taRef = useRef(null);
  const modelRef = useRef(null);
  const recognitionRef = useRef(null);
  const micStreamRef = useRef(null);
  const audioContextRef = useRef(null);
  const meterRafRef = useRef(null);
  const voiceMenuCloseTimerRef = useRef(null);
  const voiceHoldActiveRef = useRef(false);

  const handleLogoSecretClick = () => {
    if (advisoryUnlocked) return;
    const now = Date.now();
    const ref = logoClickRef.current;
    if (now - ref.lastAt > LOGO_CLICK_RESET_MS) ref.count = 0;
    ref.lastAt = now;
    ref.count += 1;
    if (ref.count < LOGO_CLICKS_NEEDED) return;
    ref.count = 0;
    setAdvisoryUnlocked(true);
    setModels((prev) => withAdvisoryOption(prev, true));
    setModelOpen(true);
  };

  useEffect(() => {
    try {
      sessionStorage.removeItem(ADVISORY_UNLOCK_KEY);
    } catch {
      /* private mode */
    }
  }, []);

  useEffect(() => {
    if (!advisoryUnlocked && selectedModel === "advisory") {
      setSelectedModel("auto_rag");
    }
  }, [advisoryUnlocked, selectedModel]);

  useEffect(() => {
    let cancelled = false;

    const sleep = (ms) => new Promise((resolve) => setTimeout(resolve, ms));

    const fetchConfig = async () => {
      const controller = new AbortController();
      const timer = setTimeout(() => controller.abort(), 8000);
      try {
        const r = await fetch(`${API}/config`, { signal: controller.signal });
        if (!r.ok) throw new Error("config unavailable");
        return r.json();
      } finally {
        clearTimeout(timer);
      }
    };

    (async () => {
      const maxAttempts = 45;
      for (let attempt = 1; attempt <= maxAttempts && !cancelled; attempt += 1) {
        try {
          const d = await fetchConfig();
          if (cancelled) return;

          const modelApiReady = d.use_mock || d.model_api_ready !== false;

          if (d.use_mock || d.openai_configured) {
            setApiKeyReady(true);
            setShowApiKeyGate(false);
            if (modelApiReady) {
              setApiConfigLoading(false);
              return;
            }
            await sleep(2000);
            continue;
          }

          setApiConfigLoading(false);
          const stored = sessionStorage.getItem(OPENAI_KEY_SESSION);
          if (stored) {
            try {
              await applyOpenAIKeyToServer(stored);
              if (!cancelled) {
                setApiKeyReady(true);
                setShowApiKeyGate(false);
              }
              return;
            } catch {
              sessionStorage.removeItem(OPENAI_KEY_SESSION);
              if (!cancelled) setApiKeyGateReason("reauth");
            }
          }

          if (!cancelled) {
            setApiKeyReady(false);
            setShowApiKeyGate(true);
          }
          return;
        } catch {
          if (cancelled) return;
          if (attempt < maxAttempts) {
            await sleep(2000);
          }
        }
      }

      if (!cancelled) {
        setApiConfigLoading(false);
        setApiKeyReady(false);
        setApiKeyGateReason("initial");
        setShowApiKeyGate(true);
      }
    })();

    return () => {
      cancelled = true;
    };
  }, []);

  useEffect(() => {
    fetch(`${API}/models`)
      .then((r) => (r.ok ? r.json() : null))
      .then((d) => {
        if (d?.models?.length) {
          setModels((prev) =>
            withAdvisoryOption(d.models, advisoryUnlocked),
          );
        }
      })
      .catch(() => {});
  }, [advisoryUnlocked]);

  useEffect(() => {
    try {
      localStorage.setItem(
        SESSIONS_STORAGE_KEY,
        JSON.stringify({
          sessions: sessionsForStorage(sessions),
          activeId,
          savedAt: new Date().toISOString(),
        }),
      );
    } catch {
      /* quota or private mode */
    }
  }, [sessions, activeId]);

  useEffect(() => {
    const close = (e) => {
      if (modelRef.current && !modelRef.current.contains(e.target))
        setModelOpen(false);
    };
    if (modelOpen) document.addEventListener("mousedown", close);
    return () => document.removeEventListener("mousedown", close);
  }, [modelOpen]);

  const theme = resolveTheme(uiSettings.appearance, dark, {
    stylized: uiSettings.stylizedLayout !== false,
  });
  const {
    t,
    css: themeCss,
    fontFamily,
    headingFont,
    composerRadius,
    chipRadius,
    logoFilter,
    logoGlow,
    logoTint,
    logoAvatarScale,
    ambientBackground,
  } = theme;
  const logoFilterCss = [logoFilter !== "none" ? logoFilter : "", logoGlow ? `drop-shadow(${logoGlow})` : ""]
    .filter(Boolean)
    .join(" ") || "none";
  const rtl = isRtlUi(uiSettings);
  const copy = (key) => tr(uiSettings, key);
  const stylized = uiSettings.stylizedLayout !== false;
  const appearance = uiSettings.appearance;
  const textTokens = textSizeTokens(uiSettings.textScale);
  const themeBackgroundUrl = stylized
    ? resolveThemeBackground(appearance, dark)
    : null;
  const decorTuning = getDecorTuningForAppearance(uiSettings, appearance);
  const welcomeDecorUrl = resolveAppearanceAsset(appearance, "welcome");
  const welcomeDecorStyle = decorImageStyle("welcome", {}, appearance);
  const profileDecorUrl = stylized
    ? resolveAppearanceAsset(appearance, "profile", {
        slot: decorTuning.profile?.slot,
      })
    : null;
  const profileDecorStyle = decorImageStyle(
    "profile",
    decorTuning.profile,
    appearance,
  );
  const composerDecorUrl = stylized
    ? resolveAppearanceAsset(appearance, "composer", {
        slot: decorTuning.composer?.slot,
      })
    : null;
  const composerDecorStyle = decorImageStyle(
    "composer",
    decorTuning.composer,
    appearance,
  );

  useEffect(() => {
    import("@fontsource/dm-sans/400.css");
    import("@fontsource/dm-sans/600.css");
    import("@fontsource/dm-sans/700.css");
  }, []);

  useEffect(() => {
    document.documentElement.lang = uiSettings.language === "ar" ? "ar" : "en";
    document.documentElement.dir = rtl ? "rtl" : "ltr";
  }, [uiSettings.language, rtl]);

  const handleUiSettingsChange = (next) => {
    setUiSettings(next);
    saveUiSettings(next);
  };

  const all = sessions.find((s) => s.id === activeId) || sessions[0];
  const filteredSessions = convSearch.trim()
    ? sessions.filter((s) => sessionMatchesSearch(s, convSearch))
    : sessions;

  const clearAutoRouteTimer = () => {
    if (autoRouteTimerRef.current) {
      clearTimeout(autoRouteTimerRef.current);
      autoRouteTimerRef.current = null;
    }
  };

  const showAutoRouteHint = (routedTo, reason) => {
    if (!routedTo) return;
    const routed = getRoutedDisplay(routedTo, {
      developerLabels: uiSettings.developerLabels,
      language: uiSettings.language,
    });
    clearAutoRouteTimer();
    setAutoRouteFading(false);
    setAutoRouteHint({
      label: routed.friendly,
      technical: routed.technical,
      reason: reason || "",
    });
    autoRouteTimerRef.current = setTimeout(() => {
      setAutoRouteFading(true);
      autoRouteTimerRef.current = setTimeout(() => {
        setAutoRouteHint(null);
        setAutoRouteFading(false);
        autoRouteTimerRef.current = null;
      }, 600);
    }, AUTO_ROUTE_HINT_MS);
  };

  useEffect(() => () => clearAutoRouteTimer(), []);

  useEffect(() => {
    if (selectedModel !== "auto_rag") {
      clearAutoRouteTimer();
      setAutoRouteHint(null);
      setAutoRouteFading(false);
    }
  }, [selectedModel]);

  useEffect(() => {
    if (selectedModel !== "auto_rag") return;
    const msgs = all?.messages || [];
    let lastBot = null;
    for (let i = msgs.length - 1; i >= 0; i--) {
      if (msgs[i].role === "bot") {
        lastBot = msgs[i];
        break;
      }
    }
    if (!lastBot) {
      setAutoRouteHint(null);
      return;
    }
    // New turn still streaming — don't show the previous answer's route.
    if (lastBot.streaming && !lastBot.routed_to) {
      setAutoRouteHint(null);
      setAutoRouteFading(false);
      return;
    }
    if (lastBot.routed_to) {
      const routed = getRoutedDisplay(lastBot.routed_to, {
        developerLabels: uiSettings.developerLabels,
        language: uiSettings.language,
      });
      setAutoRouteHint({
        label: routed.friendly,
        technical: routed.technical,
        reason: lastBot.router_reason || "",
      });
      setAutoRouteFading(false);
    }
  }, [activeId, selectedModel, all?.messages]);

  const scroll = () =>
    setTimeout(
      () => bottomRef.current?.scrollIntoView({ behavior: "smooth" }),
      50,
    );

  const addSession = () => {
    const s = newSession();
    setSessions((p) => [s, ...p]);
    setActiveId(s.id);
    setText("");
    setImage(null);
  };

  const deleteSession = (id) => {
    const filtered = sessions.filter((s) => s.id !== id);
    if (filtered.length === 0) {
      const s = newSession();
      setSessions([s]);
      setActiveId(s.id);
    } else {
      setSessions(filtered);
      if (activeId === id) setActiveId(filtered[0].id);
    }
  };

  const patch = (id, fn) =>
    setSessions((p) => p.map((s) => (s.id === id ? fn(s) : s)));

  const handleFile = async (f) => {
    if (!f || !f.type.startsWith("image/")) return;
    const b64 = await fileToBase64(f);
    setImage({
      file: f,
      base64: b64,
      mime: f.type,
      preview: URL.createObjectURL(f),
    });
  };

  const getSpeechRecognition = () =>
    globalThis.SpeechRecognition || globalThis.webkitSpeechRecognition || null;

  const openVoiceMenu = () => {
    if (voiceMenuCloseTimerRef.current) {
      clearTimeout(voiceMenuCloseTimerRef.current);
      voiceMenuCloseTimerRef.current = null;
    }
    setVoiceMenuOpen(true);
  };

  const scheduleVoiceMenuClose = () => {
    if (listening) return;
    if (voiceMenuCloseTimerRef.current) {
      clearTimeout(voiceMenuCloseTimerRef.current);
    }
    voiceMenuCloseTimerRef.current = setTimeout(() => {
      setVoiceMenuOpen(false);
      voiceMenuCloseTimerRef.current = null;
    }, 260);
  };

  const toggleVoiceMenu = () => {
    if (voiceMenuOpen) {
      setVoiceMenuOpen(false);
    } else {
      openVoiceMenu();
    }
  };

  const stopVoiceMeter = () => {
    if (meterRafRef.current) {
      cancelAnimationFrame(meterRafRef.current);
      meterRafRef.current = null;
    }
    if (micStreamRef.current) {
      micStreamRef.current.getTracks().forEach((track) => track.stop());
      micStreamRef.current = null;
    }
    if (audioContextRef.current) {
      audioContextRef.current.close().catch(() => {});
      audioContextRef.current = null;
    }
    setVoiceLevel(0);
  };

  const refreshVoiceDevices = async () => {
    if (!navigator.mediaDevices?.enumerateDevices) return;
    try {
      const devices = await navigator.mediaDevices.enumerateDevices();
      const inputs = devices.filter((device) => device.kind === "audioinput");
      setVoiceDevices(inputs);
      if (!selectedVoiceDeviceId && inputs[0]?.deviceId) {
        setSelectedVoiceDeviceId(inputs[0].deviceId);
      }
    } catch {
      /* Device labels may be unavailable until permission is granted. */
    }
  };

  const startVoiceMeter = async (deviceId = selectedVoiceDeviceId) => {
    if (!navigator.mediaDevices?.getUserMedia) return;
    stopVoiceMeter();
    const audio = deviceId
      ? { deviceId: { exact: deviceId } }
      : true;
    const stream = await navigator.mediaDevices.getUserMedia({ audio });
    micStreamRef.current = stream;
    await refreshVoiceDevices();

    const AudioCtx = globalThis.AudioContext || globalThis.webkitAudioContext;
    if (!AudioCtx) return;
    const ctx = new AudioCtx();
    const analyser = ctx.createAnalyser();
    analyser.fftSize = 256;
    ctx.createMediaStreamSource(stream).connect(analyser);
    audioContextRef.current = ctx;

    const data = new Uint8Array(analyser.frequencyBinCount);
    const tick = () => {
      analyser.getByteTimeDomainData(data);
      let sum = 0;
      for (const value of data) {
        const centered = (value - 128) / 128;
        sum += centered * centered;
      }
      const rms = Math.sqrt(sum / data.length);
      setVoiceLevel(Math.min(1, rms * 4));
      meterRafRef.current = requestAnimationFrame(tick);
    };
    tick();
  };

  const stopVoiceInput = () => {
    recognitionRef.current?.stop?.();
    recognitionRef.current = null;
    setListening(false);
    setInterimTranscript("");
    stopVoiceMeter();
  };

  const startVoiceInput = async () => {
    const SpeechRecognition = getSpeechRecognition();
    if (!SpeechRecognition) {
      setVoiceError(copy("voiceUnsupported"));
      openVoiceMenu();
      return;
    }

    try {
      setVoiceError("");
      openVoiceMenu();
      await startVoiceMeter();
      if (holdToRecord && !voiceHoldActiveRef.current) {
        stopVoiceMeter();
        return;
      }

      const recognition = new SpeechRecognition();
      recognition.lang = uiSettings.language === "ar" ? "ar-SA" : "en-US";
      recognition.interimResults = true;
      recognition.continuous = true;
      recognition.onresult = (event) => {
        let finalText = "";
        let interim = "";
        for (let i = event.resultIndex; i < event.results.length; i += 1) {
          const transcript = event.results[i][0]?.transcript || "";
          if (event.results[i].isFinal) finalText += transcript;
          else interim += transcript;
        }
        if (finalText.trim()) {
          setText((prev) =>
            [prev.trimEnd(), finalText.trim()].filter(Boolean).join(" "),
          );
        }
        setInterimTranscript(interim.trim());
      };
      recognition.onerror = (event) => {
        const error = event.error || "";
        if (error === "aborted" || error === "no-speech") {
          setVoiceError("");
          return;
        }
        if (error === "network") {
          setVoiceError("Speech recognition is unavailable here. Try Chrome, check mic permission, or type instead.");
          return;
        }
        if (error === "not-allowed" || error === "service-not-allowed") {
          setVoiceError("Microphone permission is blocked for this page.");
          return;
        }
        setVoiceError(error || "Microphone error");
      };
      recognition.onend = () => {
        recognitionRef.current = null;
        setListening(false);
        setInterimTranscript("");
        stopVoiceMeter();
      };
      recognitionRef.current = recognition;
      recognition.start();
      setListening(true);
    } catch (err) {
      setVoiceError(err?.message || "Microphone permission was denied");
      setListening(false);
      stopVoiceMeter();
    }
  };

  const handleVoiceButtonClick = () => {
    openVoiceMenu();
    if (holdToRecord) return;
    if (listening) stopVoiceInput();
    else startVoiceInput();
  };

  const handleVoicePointerDown = (event) => {
    if (!holdToRecord || event.button === 2) return;
    event.preventDefault();
    voiceHoldActiveRef.current = true;
    startVoiceInput();
  };

  const handleVoicePointerUp = () => {
    voiceHoldActiveRef.current = false;
    if (holdToRecord) stopVoiceInput();
  };

  const selectVoiceDevice = async (deviceId) => {
    setSelectedVoiceDeviceId(deviceId);
    openVoiceMenu();
    if (micStreamRef.current) {
      setTimeout(() => {
        startVoiceMeter(deviceId).catch(() => {});
      }, 0);
    }
  };

  useEffect(() => {
    if (voiceMenuOpen) refreshVoiceDevices();
  }, [voiceMenuOpen]);

  useEffect(
    () => () => {
      if (voiceMenuCloseTimerRef.current) {
        clearTimeout(voiceMenuCloseTimerRef.current);
      }
      stopVoiceInput();
    },
    [],
  );

  const buildHistory = () =>
    all.messages
      .filter(
        (m) =>
          m.role === "user" ||
          m.role === "bot" ||
          (m.role === "compare" && m.panels?.length && !m.panels[0]?.loading),
      )
      .slice(-20)
      .map((m) => {
        if (m.role === "bot") {
          return { role: "assistant", content: m.answer };
        }
        if (m.role === "compare") {
          return {
            role: "assistant",
            content: m.panels
              .map((p) => `${p.modelName}: ${p.answer || p.error || ""}`)
              .join("\n\n"),
          };
        }
        return { role: "user", content: m.text };
      })
      .filter((m) => (m.content || "").trim());

  const handleSubmit = async () => {
    if ((!text.trim() && !image) || loading || !apiKeyReady) return;
    const requestSessionId = activeId;
    const q = text.trim() || "Analyze this image";
    const img = image;
    const timeStr = formatClockTime(uiSettings.language);
    setText("");
    setImage(null);
    setLoading(true);
    setActiveRequestSessionId(requestSessionId);
    const modelForRequest = resolveRequestModel(selectedModel, advisoryUnlocked);
    if (modelForRequest === "auto_rag") {
      clearAutoRouteTimer();
      setAutoRouteHint(null);
      setAutoRouteFading(false);
    }

    const userMsg = {
      role: "user",
      text: q,
      imgPreview: img?.preview || null,
      time: timeStr,
    };
    patch(requestSessionId, (s) => ({
      ...s,
      messages: [...s.messages, userMsg],
      name:
        s.messages.length === 0
          ? q.slice(0, 38) + (q.length > 38 ? "…" : "")
          : s.name,
    }));
    scroll();

    const history = buildHistory();
    const body = {
      question: q,
      model: modelForRequest,
      crop_type: "all",
      question_type: "all",
      history,
    };
    if (img) {
      body.image_base64 = img.base64;
      body.image_mime = img.mime;
    }

    if (compareMode) {
      const compareModels = compareModelList(
        models,
        uiSettings.developerLabels,
        uiSettings.language,
      );
      const placeholderPanels = compareModels.map((m) => ({
        modelId: m.id,
        modelName: m.name,
        answer: "",
        sources: [],
        latency: 0,
        loading: true,
      }));
      patch(requestSessionId, (s) => ({
        ...s,
        messages: [
          ...s.messages,
          {
            role: "compare",
            panels: placeholderPanels,
            time: timeStr,
            latency: null,
          },
        ],
      }));
      scroll();

      try {
        const compareBody = { ...body };
        delete compareBody.model;
        const r = await fetch(`${API}/ask/compare`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(compareBody),
        });
        if (!r.ok) throw new Error(`Server error ${r.status}`);
        const d = await r.json();
        const panels = (d.results || []).map((row) => ({
          modelId: row.model,
          modelName: row.model_name || row.model,
          answer: row.answer,
          sources: row.sources || [],
          confidence: row.confidence,
          retrieval_score: row.retrieval_score,
          retrieved_chunks: row.retrieved_chunks,
          latency: row.latency_ms,
          error: row.error,
          loading: false,
        }));
        patch(requestSessionId, (s) => {
          const msgs = [...s.messages];
          const last = msgs[msgs.length - 1];
          const compareMsg = {
            role: "compare",
            panels,
            time: timeStr,
            latency: d.latency_ms,
          };
          if (last?.role === "compare" && last.panels?.[0]?.loading) {
            msgs[msgs.length - 1] = compareMsg;
          } else {
            msgs.push(compareMsg);
          }
          return { ...s, messages: msgs };
        });
      } catch (e) {
        patch(requestSessionId, (s) => {
          const msgs = [...s.messages];
          if (
            msgs[msgs.length - 1]?.role === "compare" &&
            msgs[msgs.length - 1]?.panels?.[0]?.loading
          ) {
            msgs.pop();
          }
          return {
            ...s,
            messages: [
              ...msgs,
              {
                role: "error",
                text: e.message.includes("fetch")
                  ? "Cannot connect to API. Make sure the server is running on localhost:8000"
                  : e.message,
              },
            ],
          };
        });
      } finally {
        setLoading(false);
        setActiveRequestSessionId((id) => (id === requestSessionId ? null : id));
        scroll();
      }
      return;
    }

    try {
      const askPath =
        modelForRequest === "advisory"
          ? `${API}/ask/advisory/stream`
          : `${API}/ask/stream`;

      patch(requestSessionId, (s) => ({
        ...s,
        messages: [
          ...s.messages,
          {
            role: "bot",
            answer: "",
            streaming: true,
            status: "Starting…",
            sources: [],
            model: modelForRequest,
            time: timeStr,
          },
        ],
      }));
      scroll();

      const applyStreamPatch = (updateFn) => {
        patch(requestSessionId, (s) => {
          const msgs = [...s.messages];
          const last = msgs[msgs.length - 1];
          if (last?.role !== "bot" || !last?.streaming) return s;
          msgs[msgs.length - 1] = updateFn(last);
          return { ...s, messages: msgs };
        });
        scroll();
      };

      const r = await fetch(askPath, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
      });
      if (!r.ok) throw new Error(`Server error ${r.status}`);

      let streamError = null;
      await consumeNdjsonStream(r, (ev) => {
        if (ev.event === "error") {
          streamError = new Error(ev.message || "Stream failed");
          return;
        }
        if (ev.event === "status") {
          applyStreamPatch((last) => ({
            ...last,
            status: ev.message || last.status,
            ...(ev.routed_to
              ? { routed_to: ev.routed_to, router_reason: ev.router_reason || "" }
              : {}),
          }));
          if (modelForRequest === "auto_rag" && ev.routed_to) {
            showAutoRouteHint(ev.routed_to, ev.router_reason);
          }
        }
        if (ev.event === "token") {
          applyStreamPatch((last) => ({
            ...last,
            answer: (last.answer || "") + (ev.content || ""),
            status: "",
          }));
        }
        if (ev.event === "done") {
          if (modelForRequest === "auto_rag" && ev.routed_to) {
            showAutoRouteHint(ev.routed_to, ev.router_reason);
          }
          applyStreamPatch((last) => ({
            ...last,
            streaming: false,
            status: "",
            answer: ev.answer ?? last.answer ?? "",
            sources: ev.sources || [],
            confidence: ev.confidence,
            retrieval_score: ev.retrieval_score,
            retrieved_chunks: ev.retrieved_chunks,
            model: ev.model || modelForRequest,
            routed_to: ev.routed_to,
            router_reason: ev.router_reason,
            lang: ev.detected_language,
            latency: ev.latency_ms,
            hasImage: !!img,
          }));
        }
      });

      if (streamError) throw streamError;

      patch(requestSessionId, (s) => {
        const msgs = [...s.messages];
        const last = msgs[msgs.length - 1];
        if (last?.role === "bot" && last?.streaming) {
          msgs[msgs.length - 1] = {
            ...last,
            streaming: false,
            status: "",
            answer: last.answer || "No response received.",
          };
        }
        return { ...s, messages: msgs };
      });
    } catch (e) {
      if (isOpenAIKeyError(e)) {
        sessionStorage.removeItem(OPENAI_KEY_SESSION);
        setApiKeyReady(false);
        setApiKeyGateReason("reauth");
        setApiKeyError(
          "OpenAI rejected that key. Paste the full key from platform.openai.com, not a masked or placeholder value.",
        );
        setShowApiKeyGate(true);
      }
      patch(requestSessionId, (s) => {
        const msgs = [...s.messages];
        if (
          msgs[msgs.length - 1]?.role === "bot" &&
          msgs[msgs.length - 1]?.streaming
        ) {
          msgs.pop();
        }
        return {
          ...s,
          messages: [
            ...msgs,
            {
              role: "error",
              text: e.message.includes("fetch")
                ? "Cannot connect to API. Make sure the server is running on localhost:8000"
                : e.message,
            },
          ],
        };
      });
    } finally {
      setLoading(false);
      setActiveRequestSessionId((id) => (id === requestSessionId ? null : id));
      scroll();
    }
  };

  const canSend = (text.trim() || image) && !loading && apiKeyReady && !apiConfigLoading;
  const isAr = (txt) => /[\u0600-\u06ff]/.test(txt || "");
  const activeModelLabels = getModelDisplay(selectedModel, {
    developerLabels: uiSettings.developerLabels,
    language: uiSettings.language,
  });
  const hasCompareMessages = all.messages.some((m) => m.role === "compare");
  const messagesWide = compareMode || hasCompareMessages;
  const composerWide = compareMode;
  const showBottomLoader =
    loading &&
    activeRequestSessionId === all.id &&
    !(
      all.messages[all.messages.length - 1]?.role === "bot" &&
      all.messages[all.messages.length - 1]?.streaming
    ) &&
    !(
      all.messages[all.messages.length - 1]?.role === "compare" &&
      all.messages[all.messages.length - 1]?.panels?.[0]?.loading
    );

  const handleApiKeySubmit = async () => {
    setApiKeyError("");
    setApiKeySubmitting(true);
    try {
      await applyOpenAIKeyToServer(apiKeyInput);
      sessionStorage.setItem(OPENAI_KEY_SESSION, apiKeyInput.trim());
      setGateExiting(true);
      setTimeout(() => {
        setApiKeyReady(true);
        setShowApiKeyGate(false);
        setGateExiting(false);
        setApiKeyInput("");
      }, 320);
    } catch (e) {
      sessionStorage.removeItem(OPENAI_KEY_SESSION);
      setApiKeyError(e.message || "Could not save API key");
    } finally {
      setApiKeySubmitting(false);
    }
  };

  const rootClass = [
    "tm-root",
    dark ? "" : "tm-light",
    stylized ? "tm-stylized" : "",
    showApiKeyGate || gateExiting || apiConfigLoading ? "tm-gate-open" : "",
    apiKeyReady && !showApiKeyGate && !gateExiting ? "tm-app-ready" : "",
  ]
    .filter(Boolean)
    .join(" ");

  return (
    <div
      className={rootClass}
      dir={rtl ? "rtl" : "ltr"}
      style={{
        display: "flex",
        height: "100vh",
        overflow: "hidden",
        position: "relative",
        background: t.bg,
        color: t.text1,
        fontFamily: fontFamily,
        fontSize: 14,
        "--tm-chat-font-size": `${textTokens.chat}px`,
        "--tm-user-font-size": `${textTokens.user}px`,
        "--tm-chat-meta-size": `${textTokens.meta}px`,
        "--tm-composer-font-size": `${textTokens.composer}px`,
        "--tm-accent": t.accent,
        "--tm-accent-dim": t.accentDim,
        "--tm-accent-rgb": hexToRgb(t.accent),
        "--tm-bg": t.bg,
        "--tm-bg-input": t.bgInput,
        "--tm-border1": t.border1,
        "--tm-text3": t.text3,
        "--tm-text4": t.text4,
        "--tm-logo-filter": logoFilterCss,
        "--tm-panel-general": t.panelGeneral || t.accent,
        "--tm-panel-product": t.panelProduct || t.accentWheat || "#c4a35a",
        "--tm-confidence-bg": t.confidenceBg || t.bgHover,
      }}
    >
      <div
        className="tm-ambient-layer"
        style={{
          background: themeBackgroundUrl
            ? `${ambientBackground}, url("${themeBackgroundUrl}")`
            : ambientBackground,
          ...(themeBackgroundUrl
            ? {
                backgroundSize: `cover, ${DEFAULT_BACKGROUND_LAYOUT.size}`,
                backgroundPosition: `center center, ${DEFAULT_BACKGROUND_LAYOUT.imagePosition}`,
                backgroundRepeat: "no-repeat, no-repeat",
              }
            : {}),
        }}
        aria-hidden
      />
      <div
        className="tm-shell"
        style={{ display: "flex", flex: 1, minHeight: 0, minWidth: 0, width: "100%" }}
      >
      {/* Sidebar */}
      <aside
        className="tm-sidebar-glass"
        style={{
          width: sideOpen ? SIDEBAR_WIDTH : 0,
          minWidth: sideOpen ? SIDEBAR_WIDTH : 0,
          overflow: "hidden",
          background: t.bgSide,
          ...(rtl
            ? { borderLeft: `1px solid ${t.border1}` }
            : { borderRight: `1px solid ${t.border1}` }),
          display: "flex",
          flexDirection: "column",
          transition: "width .22s ease, min-width .22s ease",
          flexShrink: 0,
          direction: rtl ? "rtl" : "ltr",
        }}
      >
        <div
          style={{
            display: "flex",
            flexDirection: "column",
            height: "100%",
            minWidth: SIDEBAR_WIDTH,
            padding: "12px 12px 16px",
          }}
        >
          <div
            style={{
              display: "flex",
              alignItems: "center",
              justifyContent: "space-between",
              marginBottom: 8,
              flexDirection: rtl ? "row-reverse" : "row",
            }}
          >
            <div
              style={{
                display: "flex",
                alignItems: "center",
                gap: 8,
                flexDirection: rtl ? "row-reverse" : "row",
              }}
            >
              <TerraLogo
                size={30}
                onSecretClick={handleLogoSecretClick}
                logoFilter={logoFilter}
                logoGlow={logoGlow}
                logoTint={logoTint}
              />
              <span style={{ fontSize: 15, fontWeight: 700, color: t.text1 }}>
                {copy("appName")}
              </span>
            </div>
          </div>

          <div
            style={{
              fontSize: 11,
              color: t.text3,
              letterSpacing: "0.1em",
              textTransform: "uppercase",
              marginBottom: 6,
              paddingInlineStart: 4,
              textAlign: "start",
            }}
          >
            {copy("conversations")}
          </div>
          <div
            className="tm-search-wrap"
            style={{
              display: "flex",
              alignItems: "center",
              gap: 6,
              marginBottom: 10,
              padding: "6px 10px",
              background: t.bgInput,
              border: `1px solid ${t.border1}`,
              borderRadius: 8,
              flexDirection: rtl ? "row-reverse" : "row",
            }}
          >
            <I.search c={t.text4} />
            <input
              type="text"
              value={convSearch}
              onChange={(e) => setConvSearch(e.target.value)}
              placeholder={copy("searchPlaceholder")}
              aria-label={copy("searchPlaceholder")}
              style={{
                flex: 1,
                minWidth: 0,
                border: "none",
                outline: "none",
                background: "transparent",
                fontFamily: fontFamily,
                fontSize: 13,
                color: t.text1,
                direction: rtl ? "rtl" : "ltr",
                textAlign: rtl ? "right" : "left",
              }}
            />
            {convSearch.trim() ? (
              <button
                type="button"
                onClick={() => setConvSearch("")}
                title={copy("searchClear")}
                aria-label={copy("searchClear")}
                style={{
                  background: "transparent",
                  border: "none",
                  cursor: "pointer",
                  padding: "0 2px",
                  fontSize: 18,
                  lineHeight: 1,
                  color: t.text3,
                  display: "flex",
                  alignItems: "center",
                }}
              >
                ×
              </button>
            ) : null}
          </div>

          <NewChatButton
            onClick={addSession}
            t={t}
            label={copy("newChat")}
            fontFamily={fontFamily}
            rtl={rtl}
          />

          <div
            style={{
              flex: 1,
              overflowY: "auto",
              display: "flex",
              flexDirection: "column",
              gap: 1,
              marginTop: 8,
              paddingInline: 2,
            }}
          >
            {filteredSessions.length === 0 ? (
              <div
                style={{
                  fontSize: 12,
                  color: t.text3,
                  padding: "12px 8px",
                  textAlign: "center",
                }}
              >
                {copy("noConversationsMatch")}
              </div>
            ) : (
              filteredSessions.map((s) => (
              <div
                key={s.id}
                className="tm-conv-item"
                onMouseEnter={() => setHover(s.id)}
                onMouseLeave={() => setHover(null)}
                style={{
                  display: "flex",
                  alignItems: "center",
                  gap: 4,
                  background:
                    s.id === activeId
                      ? t.bgActive
                      : hover === s.id
                        ? t.bgHover
                        : "transparent",
                  borderRadius: 8,
                  transition: "background .15s",
                  padding: "2px 4px 2px 0",
                }}
              >
                <button
                  onClick={() => setActiveId(s.id)}
                  style={{
                    flex: 1,
                    textAlign: rtl ? "right" : "left",
                    background: "transparent",
                    border: "none",
                    padding: "8px 8px",
                    cursor: "pointer",
                    fontFamily: fontFamily,
                    display: "flex",
                    alignItems: "center",
                    gap: 8,
                    minWidth: 0,
                    flexDirection: rtl ? "row-reverse" : "row",
                  }}
                >
                  <I.chat c={s.id === activeId ? t.accent : t.text4} />
                  <div style={{ flex: 1, minWidth: 0 }}>
                    <div
                      style={{
                        fontSize: 13,
                        fontWeight: s.id === activeId ? 600 : 400,
                        whiteSpace: "nowrap",
                        overflow: "hidden",
                        textOverflow: "ellipsis",
                        color: s.id === activeId ? t.text1 : t.text2,
                      }}
                    >
                      {s.name}
                    </div>
                    <div style={{ fontSize: 11, color: t.text4, marginTop: 1 }}>
                      {s.ts}
                    </div>
                  </div>
                </button>
                {(hover === s.id || s.id === activeId) && (
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      deleteSession(s.id);
                    }}
                    title={copy("delete")}
                    style={{
                      background: "transparent",
                      border: "none",
                      cursor: "pointer",
                      padding: 4,
                      borderRadius: 4,
                      display: "flex",
                      alignItems: "center",
                      justifyContent: "center",
                      color: t.text3,
                      transition: "color .15s",
                    }}
                    onMouseEnter={(e) =>
                      (e.currentTarget.style.color = t.err.color)
                    }
                    onMouseLeave={(e) =>
                      (e.currentTarget.style.color = t.text4)
                    }
                  >
                    <I.trash c="currentColor" />
                  </button>
                )}
              </div>
            ))
            )}
          </div>

          <div
            style={{
              marginTop: "auto",
              flexShrink: 0,
              paddingTop: 8,
              borderTop: `1px solid ${t.border1}`,
            }}
          >
            <SidebarWelcomeCard
              t={t}
              uiSettings={uiSettings}
              rtl={rtl}
              decorUrl={welcomeDecorUrl}
              decorStyle={welcomeDecorStyle}
            />
            <UserProfileMenu
              t={t}
              uiSettings={uiSettings}
              onChange={handleUiSettingsChange}
              dark={dark}
              onToggleDark={() => setDark((d) => !d)}
              rtl={rtl}
              stylized={stylized}
              profileDecorUrl={profileDecorUrl}
              profileDecorStyle={profileDecorStyle}
            />
          </div>
        </div>
      </aside>

      {/* Main */}
      <div
        style={{
          flex: 1,
          display: "flex",
          flexDirection: "column",
          minWidth: 0,
          minHeight: 0,
        }}
      >
        {/* Topbar */}
        <div
          className={`tm-topbar-glass tm-topbar${stylized ? " tm-topbar--stylized" : ""}`}
          style={{
            borderBottom: `1px solid ${t.border1}`,
            flexShrink: 0,
            ...(stylized ? {} : { background: t.bg }),
            minWidth: 0,
            position: "relative",
            zIndex: 20,
            overflow: "visible",
          }}
        >
          <div className="tm-topbar-start">
          <button
            className="tm-icon-btn"
            onClick={() => setSideOpen((o) => !o)}
            title={copy("toggleSidebar")}
            style={{
              background: "transparent",
              border: "none",
              borderRadius: 8,
              color: t.text3,
              width: 34,
              height: 34,
              cursor: "pointer",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              transition: "background .15s",
              flexShrink: 0,
            }}
            onMouseEnter={(e) => (e.currentTarget.style.background = t.bgHover)}
            onMouseLeave={(e) =>
              (e.currentTarget.style.background = "transparent")
            }
          >
            <I.sidebar />
          </button>
          <TerraLogo
            size={36}
            onSecretClick={handleLogoSecretClick}
            logoFilter={logoFilter}
            logoGlow={logoGlow}
            logoTint={logoTint}
          />
          <span
            className="tm-topbar-brand-text"
            style={{ fontSize: 14, fontWeight: 600, color: t.text1 }}
          >
            TerraMind
          </span>
          </div>

          <div
            ref={modelRef}
            className="tm-topbar-end"
            style={{
              opacity: compareMode ? 0.45 : 1,
              pointerEvents: compareMode ? "none" : "auto",
            }}
          >
            <button
              type="button"
              className="tm-model-trigger"
              onClick={() => setModelOpen((o) => !o)}
              title={compareMode ? copy("compareDisabled") : copy("chooseModel")}
              disabled={compareMode}
              style={{
                background: modelOpen ? t.bgActive : t.bgCard,
                border: `1px solid ${modelOpen ? t.accent : t.border1}`,
                cursor: "pointer",
                fontFamily: fontFamily,
                color: t.text1,
              }}
            >
              <span className="tm-model-trigger-label">
                {activeModelLabels.friendly}
              </span>
              <I.chevron c={t.text3} />
            </button>
            {selectedModel === "auto_rag" && !compareMode && (
              <AutoRouteHint
                label={autoRouteHint?.label}
                technical={autoRouteHint?.technical}
                reason={autoRouteHint?.reason}
                t={t}
                fading={autoRouteFading}
                developerLabels={uiSettings.developerLabels}
                rtl={rtl}
                usingPrefix={copy("usingMode")}
              />
            )}
            {modelOpen && (
              <div
                className="tm-model-menu"
                style={{
                  background: t.bgCard,
                  border: `1px solid ${t.border1}`,
                  boxShadow: `0 8px 24px rgba(0,0,0,${dark ? 0.45 : 0.12})`,
                }}
              >
                {withAdvisoryOption(models, advisoryUnlocked).map((m, idx, arr) => {
                  const labels = getModelDisplay(m.id, {
                    developerLabels: uiSettings.developerLabels,
                    language: uiSettings.language,
                  });
                  const desc = getModelDescription(
                    m.id,
                    uiSettings.language,
                    m.description,
                  );
                  return (
                  <button
                    key={m.id}
                    type="button"
                    className="tm-model-menu-item"
                    onClick={() => {
                      setSelectedModel(m.id);
                      setModelOpen(false);
                    }}
                    style={{
                      display: "block",
                      width: "100%",
                      textAlign: "start",
                      background:
                        m.id === selectedModel ? t.accentDim : "transparent",
                      border: "none",
                      borderRadius: 8,
                      padding: "8px 10px",
                      cursor: "pointer",
                      fontFamily: fontFamily,
                      transition: "background .15s",
                      borderBottom:
                        idx < arr.length - 1 ? `1px solid ${t.border1}` : "none",
                    }}
                    onMouseEnter={(e) => {
                      if (m.id !== selectedModel)
                        e.currentTarget.style.background = t.bgHover;
                    }}
                    onMouseLeave={(e) => {
                      if (m.id !== selectedModel)
                        e.currentTarget.style.background =
                          m.id === selectedModel ? t.accentDim : "transparent";
                    }}
                  >
                    <div
                      style={{
                        fontSize: 13,
                        fontWeight: 600,
                        color: m.id === selectedModel ? t.accent : t.text1,
                      }}
                    >
                      {labels.friendly}
                    </div>
                    <div
                      className="tm-model-menu-item-tech"
                      style={{ color: t.text4 }}
                    >
                      {labels.technical}
                    </div>
                    {(desc) && (
                      <div
                        className="tm-model-menu-item-desc"
                        style={{
                          fontSize: 11,
                          color: t.text3,
                          marginTop: 3,
                          lineHeight: 1.4,
                        }}
                      >
                        {desc}
                      </div>
                    )}
                  </button>
                  );
                })}
              </div>
            )}
          </div>
        </div>

        {/* Messages */}
        <div
          style={{ flex: 1, overflowY: "auto", overflowX: "hidden", padding: "8px 0", minHeight: 0 }}
          onDragOver={(e) => {
            if (compareMode) return;
            e.preventDefault();
            setDragOver(true);
          }}
          onDragLeave={(e) => {
            if (e.currentTarget.contains(e.relatedTarget)) return;
            setDragOver(false);
          }}
          onDrop={(e) => {
            if (compareMode) return;
            e.preventDefault();
            setDragOver(false);
            if (e.dataTransfer.files[0]) handleFile(e.dataTransfer.files[0]);
          }}
        >
          {all.messages.length === 0 ? (
            <div
              style={{
                display: "flex",
                flexDirection: "column",
                alignItems: "center",
                justifyContent: "center",
                height: "100%",
                padding: "2rem",
                textAlign: "center",
              }}
            >
              <div className="tm-empty-logo-wrap">
                <TerraLogo
                  size={100}
                  onSecretClick={handleLogoSecretClick}
                  logoFilter={logoFilter}
                  logoGlow={logoGlow}
                  logoTint={logoTint}
                />
              </div>
              <div
                className="tm-empty-title"
                style={{
                  fontSize: 28,
                  fontWeight: 700,
                  color: t.text1,
                  marginTop: 16,
                  marginBottom: 8,
                  fontFamily: headingFont,
                }}
              >
                {copy("emptyTitle")}
              </div>
              <div
                className="tm-empty-sub"
                style={{
                  fontSize: 14,
                  color: t.text3,
                  lineHeight: 1.7,
                  maxWidth: 400,
                  marginBottom: 24,
                  whiteSpace: "pre-line",
                }}
              >
                {copy("emptySub")}
              </div>
              <div
                className="tm-empty-chips"
                style={{
                  display: "flex",
                  gap: 8,
                  flexWrap: "wrap",
                  justifyContent: "center",
                }}
              >
                {[copy("emptyChip1"), copy("emptyChip2"), copy("emptyChip3")].map((s) => (
                  <button
                    key={s}
                    className="tm-chip tm-chip-dot"
                    onClick={() => {
                      setText(s);
                      taRef.current?.focus();
                    }}
                    style={{
                      background: t.bgCard,
                      border: `1px solid ${t.border1}`,
                      borderRadius: chipRadius,
                      padding: "8px 16px",
                      fontSize: 13,
                      color: t.text2,
                      cursor: "pointer",
                      fontFamily: fontFamily,
                      transition: "background .15s",
                    }}
                    onMouseEnter={(e) =>
                      (e.currentTarget.style.background = t.bgHover)
                    }
                    onMouseLeave={(e) =>
                      (e.currentTarget.style.background = t.bgCard)
                    }
                  >
                    {s}
                  </button>
                ))}
              </div>
            </div>
          ) : (
            <div
              className={`tm-content-width tm-content-width--chat${messagesWide ? " tm-content-width--wide" : ""}`}
              style={{
                margin: "0 auto",
                padding: "20px 24px 8px",
              }}
            >
              {all.messages.map((msg, i) => {
                if (msg.role === "compare")
                  return (
                    <ComparePanels
                      key={i}
                      msg={msg}
                      models={models}
                      t={t}
                      uiSettings={uiSettings}
                      isAr={isAr}
                      appearance={uiSettings.appearance}
                    />
                  );

                if (msg.role === "user")
                  return (
                    <div
                      key={i}
                      className="tm-msg-in"
                      style={{
                        display: "flex",
                        justifyContent: "flex-end",
                        marginBottom: 16,
                      }}
                    >
                      <div style={{ maxWidth: "72%" }}>
                        {msg.imgPreview && (
                          <div style={{ marginBottom: 6, textAlign: "right" }}>
                            <img
                              src={msg.imgPreview}
                              alt=""
                              style={{
                                maxWidth: 220,
                                maxHeight: 160,
                                borderRadius: 12,
                                border: `1px solid ${t.border1}`,
                                objectFit: "cover",
                                display: "block",
                                marginInlineStart: "auto",
                              }}
                            />
                          </div>
                        )}
                        {msg.text && (
                          <div
                            style={{
                              background: t.bgActive,
                              color: t.text1,
                              borderRadius: "18px 18px 4px 18px",
                              padding: "10px 16px",
                              fontSize: "var(--tm-user-font-size)",
                              lineHeight: 1.6,
                              wordBreak: "break-word",
                              direction: isAr(msg.text) ? "rtl" : "ltr",
                              textAlign: isAr(msg.text) ? "right" : "left",
                            }}
                          >
                            {msg.text}
                          </div>
                        )}
                      </div>
                    </div>
                  );

                if (msg.role === "error")
                  return (
                    <div
                      key={i}
                      className="tm-msg-in"
                      style={{
                        background: t.err.bg,
                        border: `1px solid ${t.err.b}`,
                        borderRadius: 12,
                        padding: "12px 16px",
                        marginBottom: 16,
                        fontSize: "var(--tm-chat-font-size)",
                        color: t.err.color,
                      }}
                    >
                      {msg.text}
                    </div>
                  );

                const ar = isAr(msg.answer);
                const metaIsRtl = isRtlUi(uiSettings);
                const latencyUnit = metaIsRtl ? "مللي ثانية" : "ms";
                const useAdvisoryPanels = shouldUseAdvisoryPanels(
                  msg.model,
                  msg.answer,
                );
                return (
                  <div key={i} className="tm-msg-in" style={{ marginBottom: 20 }}>
                    <div
                      style={{
                        display: "flex",
                        alignItems: "center",
                        gap: 8,
                        marginBottom: 8,
                        flexDirection: ar ? "row-reverse" : "row",
                      }}
                    >
                      <BotAvatar
                        t={t}
                        size={28}
                        logoFilter={logoFilter}
                        logoGlow={logoGlow}
                        logoTint={logoTint}
                        logoAvatarScale={logoAvatarScale}
                      />
                      <span
                        style={{
                          fontSize: "var(--tm-chat-meta-size)",
                          fontWeight: 600,
                          color: t.text2,
                        }}
                      >
                        TerraMind
                      </span>
                      <span
                        className="tm-msg-meta"
                        style={{
                          fontSize: 11,
                          color: t.text3,
                          marginInlineStart: ar ? 0 : "auto",
                          marginInlineEnd: ar ? "auto" : 0,
                          direction: metaIsRtl ? "rtl" : "ltr",
                          unicodeBidi: "isolate",
                        }}
                      >
                        {msg.time}
                        {!msg.streaming && msg.latency != null
                          ? ` · ${msg.latency}${latencyUnit}`
                          : msg.streaming
                            ? " · …"
                            : ""}
                      </span>
                    </div>
                    <div
                      style={{
                        paddingLeft: ar ? 0 : 36,
                        paddingRight: ar ? 36 : 0,
                      }}
                    >
                      {(msg.routed_to || msg.model === "auto_rag") &&
                        msg.routed_to &&
                        !msg.streaming && (
                          <RoutePill
                            routedTo={msg.routed_to}
                            routerReason={msg.router_reason}
                            t={t}
                            developerLabels={uiSettings.developerLabels}
                            language={uiSettings.language}
                            ar={ar}
                            answeredUsingLabel={copy("answeredUsing")}
                          />
                        )}
                      {uiSettings.developerLabels &&
                        !msg.streaming &&
                        !msg.routed_to &&
                        msg.model &&
                        msg.model !== "auto_rag" && (
                          <div
                            className="tm-msg-meta"
                            style={{
                              fontSize: "calc(var(--tm-chat-meta-size) - 2px)",
                              color: t.text3,
                              marginBottom: 6,
                              direction: "ltr",
                              unicodeBidi: "isolate",
                            }}
                          >
                            {getModelDisplay(msg.model, {
                              developerLabels: true,
                              language: uiSettings.language,
                            }).technical}
                          </div>
                        )}
                      {msg.streaming && msg.status && (
                        <div
                          className="tm-msg-meta"
                          style={{
                            fontSize: "var(--tm-chat-meta-size)",
                            color: t.text3,
                            marginBottom: 8,
                            fontStyle: "italic",
                          }}
                        >
                          {msg.status}
                        </div>
                      )}
                      <div style={{ fontSize: "var(--tm-chat-font-size)" }}>
                        {useAdvisoryPanels ? (
                          <AdvisoryPanels
                            answer={msg.answer}
                            t={t}
                            ar={ar}
                            appearance={uiSettings.appearance}
                            streaming={msg.streaming}
                          />
                        ) : (
                          <>
                            <MarkdownMessage
                              content={msg.answer}
                              theme={t}
                              dir={ar ? "rtl" : "ltr"}
                            />
                            {msg.streaming && (
                              <span
                                style={{
                                  display: "inline-block",
                                  width: 8,
                                  height: 14,
                                  marginLeft: 2,
                                  background: t.accent,
                                  opacity: 0.7,
                                  verticalAlign: "text-bottom",
                                  animation: "blink 1s step-end infinite",
                                }}
                              />
                            )}
                          </>
                        )}
                      </div>
                      {uiSettings.showConfidence && msg.role === "bot" && (
                        <ConfidenceBadge
                          confidence={msg.confidence}
                          retrievalScore={msg.retrieval_score}
                          retrievedChunks={msg.retrieved_chunks}
                          routedTo={msg.routed_to}
                          modelId={msg.routed_to || msg.model || selectedModel}
                          t={t}
                          ar={ar}
                          appearance={uiSettings.appearance}
                        />
                      )}
                      {uiSettings.showSources && msg.sources?.length > 0 && (
                        <SourceList
                          sources={msg.sources}
                          t={t}
                          ar={ar}
                          appearance={uiSettings.appearance}
                        />
                      )}
                    </div>
                  </div>
                );
              })}
              {showBottomLoader && (
                <div
                  style={{
                    display: "flex",
                    alignItems: "center",
                    gap: 8,
                    marginBottom: 16,
                  }}
                >
                  <BotAvatar
                    t={t}
                    size={28}
                    logoFilter={logoFilter}
                    logoGlow={logoGlow}
                    logoTint={logoTint}
                    logoAvatarScale={logoAvatarScale}
                  />
                  <div style={{ display: "flex", gap: 4 }}>
                    {[0, 1, 2].map((i) => (
                      <div
                        key={i}
                        style={{
                          width: 7,
                          height: 7,
                          borderRadius: "50%",
                          background: t.text4,
                          animation: `dot .9s ${i * 0.2}s ease-in-out infinite`,
                        }}
                      />
                    ))}
                  </div>
                </div>
              )}
              <div ref={bottomRef} />
            </div>
          )}
        </div>

        {/* Input */}
        <div
          className={stylized ? "tm-input-footer tm-input-footer--stylized" : "tm-input-footer"}
          style={{ padding: "12px 16px 16px", flexShrink: 0 }}
        >
          <div
            className={`tm-content-width tm-content-width--composer${composerWide ? " tm-content-width--wide" : ""}`}
            style={{ margin: "0 auto" }}
          >
            <div className="tm-composer-wrap">
              {composerDecorUrl ? (
                <img
                  src={composerDecorUrl}
                  alt=""
                  aria-hidden
                  className="tm-composer-decor tm-decor-img tm-decor-fixed"
                  style={composerDecorStyle}
                />
              ) : null}
            <div
              className={`tm-composer${compareMode ? " tm-composer--compare" : ""}${dragOver ? " tm-composer--drag" : ""}${stylized ? " tm-composer--stylized" : ""}`}
              style={{
                ...(stylized ? {} : { background: t.bgInput }),
                border: `2px solid ${compareMode || dragOver ? t.accent : t.inputBorder}`,
                borderRadius: composerRadius,
                padding: "12px 14px 10px",
                display: "flex",
                flexDirection: "column",
                gap: 10,
              }}
            >
              {dragOver && (
                <div className="tm-composer-drop-overlay" aria-live="polite">
                  {copy("dropImage")}
                </div>
              )}
              {image && (
                <div
                  className="tm-composer-attachment"
                  style={{
                    background: `color-mix(in srgb, ${t.bg} 55%, transparent)`,
                    borderColor: t.border1,
                  }}
                >
                  <img
                    src={image.preview}
                    alt=""
                    className="tm-composer-attachment-thumb"
                    style={{ borderColor: t.border1 }}
                  />
                  <div style={{ flex: 1, minWidth: 0 }}>
                    <div
                      className="tm-composer-attachment-name"
                      style={{ color: t.text2 }}
                    >
                      {image.file.name}
                    </div>
                    <div
                      className="tm-composer-attachment-meta"
                      style={{ color: t.text4 }}
                    >
                      {(image.file.size / 1024).toFixed(0)} KB
                    </div>
                  </div>
                  <button
                    type="button"
                    className="tm-composer-attachment-remove"
                    onClick={() => setImage(null)}
                    style={{ color: t.text4 }}
                    aria-label={copy("delete")}
                  >
                    ✕
                  </button>
                </div>
              )}
              <textarea
                ref={taRef}
                rows={3}
                placeholder={
                  compareMode
                    ? copy("composerCompare")
                    : copy("composerPlaceholder")
                }
                value={text}
                onChange={(e) => setText(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === "Enter" && !e.shiftKey) {
                    e.preventDefault();
                    handleSubmit();
                  }
                }}
                style={{
                  background: "transparent",
                  border: "none",
                  outline: "none",
                  color: t.text1,
                  fontFamily: fontFamily,
                  fontSize: "var(--tm-composer-font-size)",
                  lineHeight: 1.6,
                  resize: "none",
                  width: "100%",
                  padding: 0,
                  direction:
                    isAr(text) || rtl ? "rtl" : "ltr",
                }}
              />
              <div
                style={{
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "space-between",
                }}
              >
                <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
                  <button
                    type="button"
                    className={`tm-composer-btn tm-composer-btn--compare${compareMode ? " tm-composer-btn--active" : ""}`}
                    onClick={() => setCompareMode((c) => !c)}
                    title={copy("compare")}
                    aria-pressed={compareMode}
                    style={{
                      fontFamily: fontFamily,
                      color: compareMode ? t.accent : t.text3,
                    }}
                  >
                    <I.columns c={compareMode ? t.accent : t.text3} />
                    <span className="tm-composer-btn-label">{copy("compare")}</span>
                  </button>
                  <input
                    ref={fileRef}
                    type="file"
                    accept="image/*"
                    style={{ display: "none" }}
                    onChange={(e) => {
                      if (e.target.files[0]) handleFile(e.target.files[0]);
                      e.target.value = "";
                    }}
                  />
                  <button
                    type="button"
                    className={`tm-composer-btn tm-composer-btn--icon${image ? " tm-composer-btn--active" : ""}`}
                    onClick={() => fileRef.current?.click()}
                    title={copy("addImage")}
                    aria-pressed={!!image}
                    style={{
                      color: image ? t.accent : t.text3,
                    }}
                  >
                    <I.img c={image ? t.accent : t.text3} />
                  </button>
                </div>
                <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
                  <div
                    className={`tm-voice-control${voiceMenuOpen ? " tm-voice-control--open" : ""}`}
                    onMouseEnter={openVoiceMenu}
                    onMouseLeave={scheduleVoiceMenuClose}
                    onFocus={openVoiceMenu}
                  >
                    <button
                      type="button"
                      className={`tm-voice-trigger${listening ? " tm-voice-trigger--active" : ""}`}
                      onClick={handleVoiceButtonClick}
                      onPointerDown={handleVoicePointerDown}
                      onPointerUp={handleVoicePointerUp}
                      onPointerCancel={handleVoicePointerUp}
                      title={holdToRecord ? copy("voiceHoldToRecord") : copy("voiceClickToToggle")}
                      aria-label={copy("voiceInput")}
                      aria-pressed={listening}
                      style={{
                        color: listening ? t.accent : t.text3,
                        borderColor: listening ? t.accent : t.border1,
                      }}
                    >
                      <I.mic c={listening ? t.accent : t.text3} />
                      <span
                        className="tm-voice-trigger-arrow"
                        onPointerDown={(event) => event.stopPropagation()}
                        onClick={(event) => {
                          event.stopPropagation();
                          toggleVoiceMenu();
                        }}
                        aria-hidden="true"
                      >
                        ▾
                      </span>
                    </button>

                    {voiceMenuOpen && (
                      <div
                        className="tm-voice-menu"
                        role="menu"
                        onMouseEnter={openVoiceMenu}
                        onMouseLeave={scheduleVoiceMenuClose}
                        style={{
                          background: `color-mix(in srgb, ${t.bgCard} 92%, transparent)`,
                          borderColor: t.border1,
                          color: t.text1,
                        }}
                      >
                        <div className="tm-voice-meter-row" style={{ color: t.text3 }}>
                          <I.mic c={listening ? t.accent : t.text3} />
                          <div
                            className="tm-voice-meter"
                            style={{
                              background: `color-mix(in srgb, ${t.text4} 22%, transparent)`,
                            }}
                          >
                            <div
                              className="tm-voice-meter-fill"
                              style={{
                                width: `${Math.round(voiceLevel * 100)}%`,
                                background: t.accent,
                              }}
                            />
                          </div>
                          {listening && (
                            <span className="tm-voice-live" style={{ color: t.accent }}>
                              {copy("voiceListening")}
                            </span>
                          )}
                        </div>

                        <div className="tm-voice-section-label" style={{ color: t.text3 }}>
                          {copy("voiceDevices")}
                        </div>
                        <div className="tm-voice-device-list">
                          {voiceDevices.length ? (
                            voiceDevices.map((device, index) => {
                              const selected = device.deviceId === selectedVoiceDeviceId;
                              return (
                                <button
                                  key={device.deviceId || index}
                                  type="button"
                                  className="tm-voice-device"
                                  onClick={() => selectVoiceDevice(device.deviceId)}
                                  style={{
                                    color: selected ? t.text1 : t.text2,
                                  }}
                                  role="menuitemradio"
                                  aria-checked={selected}
                                >
                                  <span>{device.label || `Microphone ${index + 1}`}</span>
                                  {selected && <I.check c={t.accent} />}
                                </button>
                              );
                            })
                          ) : (
                            <div className="tm-voice-empty" style={{ color: t.text3 }}>
                              {voiceError || copy("voiceNoDevices")}
                            </div>
                          )}
                        </div>

                        {interimTranscript && (
                          <div className="tm-voice-interim" style={{ color: t.text3 }}>
                            {interimTranscript}
                          </div>
                        )}
                        {voiceError && voiceDevices.length > 0 && (
                          <div className="tm-voice-error" style={{ color: t.text3 }}>
                            {voiceError}
                          </div>
                        )}

                        <button
                          type="button"
                          className="tm-voice-hold-row"
                          onClick={() => setHoldToRecord((v) => !v)}
                          role="menuitemcheckbox"
                          aria-checked={holdToRecord}
                          style={{
                            borderTopColor: t.border1,
                            color: t.text1,
                          }}
                        >
                          <span>{holdToRecord ? copy("voiceHoldToRecord") : copy("voiceClickToToggle")}</span>
                          <span
                            className={`tm-voice-switch${holdToRecord ? " tm-voice-switch--on" : ""}`}
                            style={{
                              background: holdToRecord ? t.accent : t.bgHover,
                            }}
                          >
                            <span />
                          </span>
                        </button>
                      </div>
                    )}
                  </div>

                  <button
                    type="button"
                    className={`tm-composer-send${canSend ? " tm-composer-send--ready" : ""}`}
                    onClick={handleSubmit}
                    disabled={!canSend}
                    title={copy("sendHint")}
                    style={{
                      cursor: canSend ? "pointer" : "not-allowed",
                      background: canSend ? t.accent : t.bgHover,
                      color: canSend ? "#fff" : t.text4,
                    }}
                  >
                    <I.send on={!!canSend} c={canSend ? "#fff" : t.text4} />
                  </button>
                </div>
              </div>
            </div>
            </div>
            <div
              style={{
                fontSize: 11,
                color: t.text3,
                textAlign: "center",
                marginTop: 6,
              }}
            >
              {compareMode
                ? copy("compareHint")
                : copy("sendHint")}
            </div>
          </div>
        </div>
      </div>
      </div>

      <style>{`
        ${themeCss}
        @keyframes dot{0%,100%{opacity:.25;transform:scale(.75)}50%{opacity:1;transform:scale(1)}}
        @keyframes blink{50%{opacity:0}}
        *,*::before,*::after{box-sizing:border-box;margin:0;padding:0}
        body{-webkit-font-smoothing:antialiased}
        ::-webkit-scrollbar{width:5px}
        ::-webkit-scrollbar-thumb{background:rgba(128,128,128,.2);border-radius:3px}
        textarea{scrollbar-width:none}
        textarea::-webkit-scrollbar{display:none}
        input[type="search"]::-webkit-search-cancel-button{display:none}
        input[type="search"]::-webkit-search-decoration{display:none}
      `}</style>
      <ApiKeyGate
        t={t}
        open={showApiKeyGate}
        exiting={gateExiting}
        reason={apiKeyGateReason}
        value={apiKeyInput}
        onChange={setApiKeyInput}
        onSubmit={handleApiKeySubmit}
        submitting={apiKeySubmitting}
        error={apiKeyError}
        logoFilter={logoFilter}
        logoGlow={logoGlow}
        logoTint={logoTint}
      />
      {apiConfigLoading ? (
        <BootstrapOverlay
          t={t}
          logoFilter={logoFilter}
          logoGlow={logoGlow}
          logoTint={logoTint}
        />
      ) : null}
    </div>
  );
}
