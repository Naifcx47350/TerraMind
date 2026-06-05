import { useState, useRef, useEffect } from "react";
import logoSrc from "@assets/logo/TM_Logo.png";
import { MarkdownMessage } from "./MarkdownMessage";
import { resolveTheme } from "./theme/index.js";
import { loadUiSettings, saveUiSettings } from "./settings/uiSettings.js";
import { getModelDisplay, getRoutedDisplay } from "./settings/modelLabels.js";
import { SettingsPanel } from "./components/SettingsPanel.jsx";
import { SourceList } from "./components/SourceList.jsx";
import { ConfidenceBadge } from "./components/ConfidenceBadge.jsx";
import { AdvisoryPanels, shouldUseAdvisoryPanels } from "./components/AdvisoryPanels.jsx";
import { RoutePill } from "./components/RoutePill.jsx";
import { BotAvatar } from "./components/BotAvatar.jsx";

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

function TerraLogo({ size = 1000, style = {}, onSecretClick }) {
  const img = (
    <img
      src={logoSrc}
      alt="TerraMind"
      width={size}
      height={size}
      style={{ objectFit: "contain", display: "block", ...style }}
    />
  );
  if (!onSecretClick) return img;
  return (
    <button
      type="button"
      onClick={onSecretClick}
      aria-label="TerraMind"
      style={{
        background: "none",
        border: "none",
        padding: 0,
        margin: 0,
        cursor: "default",
        lineHeight: 0,
        display: "block",
      }}
    >
      {img}
    </button>
  );
}

/** Same three backends as terramind.models.COMPARE_MODEL_IDS (Auto excluded). */
const COMPARE_MODEL_IDS = ["product_rag", "general_rag", "base_llm"];

function compareModelList(modelList, developerLabels = false) {
  const byId = Object.fromEntries(modelList.map((m) => [m.id, m]));
  return COMPARE_MODEL_IDS.map((id) => {
    const fromApi = byId[id];
    const labels = getModelDisplay(id, { developerLabels });
    return {
      id,
      name: labels.friendly,
      technical: labels.technical,
      description: fromApi?.description || labels.description || "",
    };
  });
}

const AUTO_ROUTE_HINT_MS = 10000;

function AutoRouteHint({ label, technical, reason, t, fading, developerLabels }) {
  if (!label) return null;
  return (
    <div
      title={reason || ""}
      style={{
        fontSize: 10,
        color: t.text4,
        lineHeight: 1.3,
        maxWidth: 220,
        textAlign: "right",
        opacity: fading ? 0 : 1,
        transition: "opacity 0.6s ease",
        pointerEvents: "none",
      }}
    >
      Using {label}
      {developerLabels && technical && (
        <div style={{ fontSize: 9, color: t.text4, marginTop: 1 }}>{technical}</div>
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
  const compareModels = compareModelList(models, uiSettings.developerLabels);
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
          color: t.text4,
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
                  <div style={{ fontSize: 10, color: t.text4, marginTop: 2, lineHeight: 1.3 }}>
                    {compareModels.find((m) => m.id === panel.modelId).technical}
                  </div>
                )}
                {panel.latency != null && !panel.loading && (
                  <div style={{ fontSize: 11, color: t.text4, marginTop: 2 }}>
                    {panel.latency}ms
                  </div>
                )}
              </div>
              <div
                style={{
                  flex: 1,
                  padding: "12px",
                  fontSize: 13,
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

function newSession() {
  return {
    id: Date.now(),
    name: "New conversation",
    messages: [],
    ts: new Date().toLocaleTimeString([], {
      hour: "2-digit",
      minute: "2-digit",
    }),
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
            <TerraLogo size={36} />
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
  const [convSearch, setConvSearch] = useState("");
  const [apiKeyReady, setApiKeyReady] = useState(false);
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
    (async () => {
      try {
        const r = await fetch(`${API}/config`);
        if (!r.ok) throw new Error("config unavailable");
        const d = await r.json();
        if (cancelled) return;
        if (d.use_mock || d.openai_configured) {
          setApiKeyReady(true);
          setShowApiKeyGate(false);
          return;
        }
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
      } catch {
        if (!cancelled) {
          setApiKeyReady(false);
          setApiKeyGateReason("initial");
          setShowApiKeyGate(true);
        }
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

  const theme = resolveTheme(uiSettings.appearance, dark);
  const { t, css: themeCss, fontFamily, headingFont, useMonogramAvatar, composerRadius, chipRadius } =
    theme;

  useEffect(() => {
    if (uiSettings.appearance !== "field") return;
    import("@fontsource/dm-sans/400.css");
    import("@fontsource/dm-sans/600.css");
    import("@fontsource/dm-sans/700.css");
  }, [uiSettings.appearance]);

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
    });
    clearAutoRouteTimer();
    setAutoRouteFading(false);
    setAutoRouteHint({
      label: routed.label,
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
      });
      setAutoRouteHint({
        label: routed.label,
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
    const q = text.trim() || "Analyze this image";
    const img = image;
    const timeStr = new Date().toLocaleTimeString([], {
      hour: "2-digit",
      minute: "2-digit",
    });
    setText("");
    setImage(null);
    setLoading(true);
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
    patch(activeId, (s) => ({
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
      const compareModels = compareModelList(models, uiSettings.developerLabels);
      const placeholderPanels = compareModels.map((m) => ({
        modelId: m.id,
        modelName: m.name,
        answer: "",
        sources: [],
        latency: 0,
        loading: true,
      }));
      patch(activeId, (s) => ({
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
        patch(activeId, (s) => {
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
        patch(activeId, (s) => {
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
        scroll();
      }
      return;
    }

    try {
      const askPath =
        modelForRequest === "advisory"
          ? `${API}/ask/advisory/stream`
          : `${API}/ask/stream`;

      patch(activeId, (s) => ({
        ...s,
        messages: [
          ...s.messages,
          {
            role: "bot",
            answer: "",
            streaming: true,
            status: "Starting…",
            sources: [],
            time: timeStr,
          },
        ],
      }));
      scroll();

      const applyStreamPatch = (updateFn) => {
        patch(activeId, (s) => {
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

      patch(activeId, (s) => {
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
      patch(activeId, (s) => {
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
      scroll();
    }
  };

  const canSend = (text.trim() || image) && !loading && apiKeyReady;
  const isAr = (txt) => /[\u0600-\u06ff]/.test(txt || "");
  const activeModelLabels = getModelDisplay(selectedModel, {
    developerLabels: uiSettings.developerLabels,
  });
  const hasCompareMessages = all.messages.some((m) => m.role === "compare");
  const showBottomLoader =
    loading &&
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
      setApiKeyError(e.message || "Could not save API key");
    } finally {
      setApiKeySubmitting(false);
    }
  };

  const rootClass = [
    "tm-root",
    showApiKeyGate || gateExiting ? "tm-gate-open" : "",
    apiKeyReady && !showApiKeyGate && !gateExiting ? "tm-app-ready" : "",
  ]
    .filter(Boolean)
    .join(" ");

  return (
    <div
      className={rootClass}
      style={{
        display: "flex",
        height: "100vh",
        overflow: "hidden",
        background: t.bg,
        color: t.text1,
        fontFamily: fontFamily,
        fontSize: 14,
        "--tm-accent": t.accent,
        "--tm-accent-dim": t.accentDim,
        "--tm-panel-general": t.panelGeneral || t.accent,
        "--tm-panel-product": t.panelProduct || t.accentWheat || "#c4a35a",
        "--tm-confidence-bg": t.confidenceBg || t.bgHover,
      }}
    >
      <div className="tm-shell">
      {/* Sidebar */}
      <aside
        style={{
          width: sideOpen ? 260 : 0,
          minWidth: sideOpen ? 260 : 0,
          overflow: "hidden",
          background: t.bgSide,
          borderRight: `1px solid ${t.border1}`,
          display: "flex",
          flexDirection: "column",
          transition: "width .22s ease, min-width .22s ease",
          flexShrink: 0,
        }}
      >
        <div
          style={{
            display: "flex",
            flexDirection: "column",
            height: "100%",
            minWidth: 260,
            padding: "12px 12px 16px",
          }}
        >
          <div
            style={{
              display: "flex",
              alignItems: "center",
              justifyContent: "space-between",
              marginBottom: 12,
            }}
          >
            <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
              <TerraLogo size={30} onSecretClick={handleLogoSecretClick} />
              <span style={{ fontSize: 15, fontWeight: 700, color: t.text1 }}>
                TerraMind
              </span>
            </div>
            <button
              onClick={addSession}
              title="New conversation"
              style={{
                background: "transparent",
                border: `1px solid ${t.border1}`,
                borderRadius: 8,
                color: t.text3,
                width: 32,
                height: 32,
                cursor: "pointer",
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                transition: "background .15s",
              }}
              onMouseEnter={(e) =>
                (e.currentTarget.style.background = t.bgHover)
              }
              onMouseLeave={(e) =>
                (e.currentTarget.style.background = "transparent")
              }
            >
              <I.plus />
            </button>
          </div>

          <div
            style={{
              fontSize: 11,
              color: t.text4,
              letterSpacing: "0.1em",
              textTransform: "uppercase",
              marginBottom: 6,
              paddingLeft: 4,
            }}
          >
            Conversations
          </div>
          <div
            style={{
              display: "flex",
              alignItems: "center",
              gap: 6,
              marginBottom: 8,
              padding: "6px 10px",
              background: t.bgInput,
              border: `1px solid ${t.border1}`,
              borderRadius: 8,
            }}
          >
            <I.search c={t.text4} />
            <input
              type="search"
              value={convSearch}
              onChange={(e) => setConvSearch(e.target.value)}
              placeholder="Search conversations…"
              aria-label="Search conversations"
              style={{
                flex: 1,
                minWidth: 0,
                border: "none",
                outline: "none",
                background: "transparent",
                fontFamily: fontFamily,
                fontSize: 13,
                color: t.text1,
              }}
            />
            {convSearch.trim() && (
              <button
                type="button"
                onClick={() => setConvSearch("")}
                title="Clear search"
                aria-label="Clear search"
                style={{
                  background: "transparent",
                  border: "none",
                  cursor: "pointer",
                  padding: 0,
                  fontSize: 16,
                  lineHeight: 1,
                  color: t.text4,
                }}
              >
                ×
              </button>
            )}
          </div>
          <div
            style={{
              flex: 1,
              overflowY: "auto",
              display: "flex",
              flexDirection: "column",
              gap: 1,
            }}
          >
            {filteredSessions.length === 0 ? (
              <div
                style={{
                  fontSize: 12,
                  color: t.text4,
                  padding: "12px 8px",
                  textAlign: "center",
                }}
              >
                No conversations match
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
                    textAlign: "left",
                    background: "transparent",
                    border: "none",
                    padding: "8px 8px",
                    cursor: "pointer",
                    fontFamily: fontFamily,
                    display: "flex",
                    alignItems: "center",
                    gap: 8,
                    minWidth: 0,
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
                    title="Delete"
                    style={{
                      background: "transparent",
                      border: "none",
                      cursor: "pointer",
                      padding: 4,
                      borderRadius: 4,
                      display: "flex",
                      alignItems: "center",
                      justifyContent: "center",
                      color: t.text4,
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
            style={{ borderTop: `1px solid ${t.border1}`, margin: "10px 0" }}
          />

          <SettingsPanel
            t={t}
            uiSettings={uiSettings}
            onChange={handleUiSettingsChange}
            dark={dark}
            onToggleDark={() => setDark((d) => !d)}
          />
        </div>
      </aside>

      {/* Main */}
      <div
        style={{
          flex: 1,
          display: "flex",
          flexDirection: "column",
          overflow: "hidden",
          minWidth: 0,
        }}
      >
        {/* Topbar */}
        <div
          style={{
            height: 50,
            borderBottom: `1px solid ${t.border1}`,
            display: "flex",
            alignItems: "center",
            padding: "0 16px",
            gap: 12,
            flexShrink: 0,
            background: t.bg,
          }}
        >
          <button
            className="tm-icon-btn"
            onClick={() => setSideOpen((o) => !o)}
            title="Toggle sidebar"
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
            }}
            onMouseEnter={(e) => (e.currentTarget.style.background = t.bgHover)}
            onMouseLeave={(e) =>
              (e.currentTarget.style.background = "transparent")
            }
          >
            <I.sidebar />
          </button>
          <TerraLogo size={40} onSecretClick={handleLogoSecretClick} />
          <span style={{ fontSize: 14, fontWeight: 600, color: t.text1 }}>
            TerraMind
          </span>

          <div
            ref={modelRef}
            style={{
              marginLeft: "auto",
              display: "flex",
              flexDirection: "column",
              alignItems: "flex-end",
              gap: 3,
              position: "relative",
              opacity: compareMode ? 0.45 : 1,
              pointerEvents: compareMode ? "none" : "auto",
            }}
          >
            <button
              type="button"
              onClick={() => setModelOpen((o) => !o)}
              title={compareMode ? "Disabled in compare mode" : "Choose model"}
              disabled={compareMode}
              style={{
                display: "flex",
                alignItems: "center",
                gap: 8,
                background: modelOpen ? t.bgActive : t.bgCard,
                border: `1px solid ${modelOpen ? t.accent : t.border1}`,
                borderRadius: 10,
                padding: "6px 12px",
                cursor: "pointer",
                fontFamily: fontFamily,
                color: t.text1,
                transition: "border-color .15s, background .15s",
              }}
            >
              <span
                style={{
                  fontSize: 13,
                  fontWeight: 600,
                  maxWidth: 200,
                  whiteSpace: "nowrap",
                  overflow: "hidden",
                  textOverflow: "ellipsis",
                }}
              >
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
              />
            )}
            {modelOpen && (
              <div
                className="tm-model-menu"
                style={{
                  position: "absolute",
                  top: "calc(100% + 6px)",
                  right: 0,
                  minWidth: 280,
                  background: t.bgCard,
                  border: `1px solid ${t.border1}`,
                  borderRadius: 12,
                  boxShadow: `0 8px 24px rgba(0,0,0,${dark ? 0.45 : 0.12})`,
                  padding: 6,
                  zIndex: 50,
                }}
              >
                {withAdvisoryOption(models, advisoryUnlocked).map((m) => {
                  const labels = getModelDisplay(m.id, {
                    developerLabels: uiSettings.developerLabels,
                  });
                  return (
                  <button
                    key={m.id}
                    type="button"
                    onClick={() => {
                      setSelectedModel(m.id);
                      setModelOpen(false);
                    }}
                    style={{
                      display: "block",
                      width: "100%",
                      textAlign: "left",
                      background:
                        m.id === selectedModel ? t.accentDim : "transparent",
                      border: "none",
                      borderRadius: 8,
                      padding: "10px 12px",
                      cursor: "pointer",
                      fontFamily: fontFamily,
                      transition: "background .15s",
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
                      style={{
                        fontSize: 10,
                        color: t.text4,
                        marginTop: 2,
                        lineHeight: 1.35,
                      }}
                    >
                      {labels.technical}
                    </div>
                    {(m.description || labels.description) && (
                      <div
                        style={{
                          fontSize: 11,
                          color: t.text3,
                          marginTop: 3,
                          lineHeight: 1.4,
                        }}
                      >
                        {m.description || labels.description}
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
          style={{ flex: 1, overflowY: "auto", padding: "8px 0" }}
          onDragOver={(e) => {
            e.preventDefault();
            setDragOver(true);
          }}
          onDragLeave={() => setDragOver(false)}
          onDrop={(e) => {
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
              <div className="tm-empty-logo">
                <TerraLogo size={100} onSecretClick={handleLogoSecretClick} />
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
                Ask the field.
              </div>
              <div
                className="tm-empty-sub"
                style={{
                  fontSize: 14,
                  color: t.text3,
                  lineHeight: 1.7,
                  maxWidth: 400,
                  marginBottom: 24,
                }}
              >
                Crop diseases · Pesticide guidance · Agronomy
                <br />
                Type in any language or upload a plant photo.
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
                {[
                  "Brown spots on tomato leaves?",
                  "ما علاج الصدأ في القمح؟",
                  "Best irrigation for corn?",
                ].map((s) => (
                  <button
                    key={s}
                    className="tm-chip"
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
              style={{
                maxWidth:
                  hasCompareMessages || compareMode ? "min(100%, 1280px)" : 720,
                margin: "0 auto",
                padding: "20px 24px 8px",
                width: "100%",
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
                                marginLeft: "auto",
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
                              fontSize: 14,
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
                        fontSize: 13,
                        color: t.err.color,
                      }}
                    >
                      {msg.text}
                    </div>
                  );

                const ar = isAr(msg.answer);
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
                        useMonogram={useMonogramAvatar}
                        size={28}
                      />
                      <span
                        style={{
                          fontSize: 13,
                          fontWeight: 600,
                          color: t.text2,
                        }}
                      >
                        TerraMind
                      </span>
                      <span
                        style={{
                          fontSize: 11,
                          color: t.text4,
                          marginLeft: ar ? 0 : "auto",
                          marginRight: ar ? "auto" : 0,
                        }}
                      >
                        {msg.time}
                        {!msg.streaming && msg.latency != null
                          ? ` · ${msg.latency}ms`
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
                            ar={ar}
                          />
                        )}
                      {uiSettings.developerLabels &&
                        msg.model &&
                        msg.model !== "auto_rag" &&
                        !msg.streaming && (
                          <div
                            style={{
                              fontSize: 10,
                              color: t.text4,
                              marginBottom: 6,
                            }}
                          >
                            {getModelDisplay(msg.model).technical}
                          </div>
                        )}
                      {msg.streaming && msg.status && (
                        <div
                          style={{
                            fontSize: 12,
                            color: t.text4,
                            marginBottom: 8,
                            fontStyle: "italic",
                          }}
                        >
                          {msg.status}
                        </div>
                      )}
                      <div style={{ fontSize: 14 }}>
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
                  <BotAvatar t={t} useMonogram={useMonogramAvatar} size={28} />
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
          style={{ padding: "12px 16px 16px", background: t.bg, flexShrink: 0 }}
        >
          <div
            style={{
              maxWidth:
                compareMode || hasCompareMessages ? "min(100%, 1280px)" : 720,
              margin: "0 auto",
              width: "100%",
            }}
          >
            {image && (
              <div
                style={{
                  display: "flex",
                  alignItems: "center",
                  gap: 10,
                  marginBottom: 8,
                  padding: "8px 10px",
                  background: t.bgCard,
                  border: `1px solid ${t.border1}`,
                  borderRadius: 10,
                }}
              >
                <img
                  src={image.preview}
                  alt=""
                  style={{
                    width: 44,
                    height: 44,
                    objectFit: "cover",
                    borderRadius: 8,
                    border: `1px solid ${t.border1}`,
                  }}
                />
                <div style={{ flex: 1, minWidth: 0 }}>
                  <div
                    style={{
                      fontSize: 13,
                      color: t.text2,
                      whiteSpace: "nowrap",
                      overflow: "hidden",
                      textOverflow: "ellipsis",
                    }}
                  >
                    {image.file.name}
                  </div>
                  <div style={{ fontSize: 11, color: t.text4 }}>
                    {(image.file.size / 1024).toFixed(0)} KB
                  </div>
                </div>
                <button
                  onClick={() => setImage(null)}
                  style={{
                    background: "transparent",
                    border: "none",
                    cursor: "pointer",
                    color: t.text4,
                    padding: 4,
                    fontSize: 16,
                    lineHeight: 1,
                  }}
                >
                  ✕
                </button>
              </div>
            )}
            {dragOver && (
              <div
                style={{
                  textAlign: "center",
                  padding: 12,
                  marginBottom: 8,
                  border: `2px dashed ${t.accent}`,
                  borderRadius: 10,
                  color: t.accent,
                  fontSize: 13,
                }}
              >
                Drop image here
              </div>
            )}

            <div
              className="tm-composer"
              style={{
                background: t.bgInput,
                border: `2px solid ${t.inputBorder}`,
                borderRadius: composerRadius,
                padding: "12px 14px 10px",
                display: "flex",
                flexDirection: "column",
                gap: 10,
                boxShadow: `0 1px 6px rgba(0,0,0,${dark ? 0.15 : 0.06})`,
              }}
            >
              <textarea
                ref={taRef}
                rows={3}
                placeholder={
                  compareMode
                    ? "Same question to all 3 models…"
                    : "Ask in any language • اسأل بأي لغة…"
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
                  fontSize: 14,
                  lineHeight: 1.6,
                  resize: "none",
                  width: "100%",
                  padding: 0,
                  direction: isAr(text) ? "rtl" : "ltr",
                }}
              />
              <div
                style={{
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "space-between",
                }}
              >
                <div style={{ display: "flex", alignItems: "center", gap: 6 }}>
                  <button
                    type="button"
                    onClick={() => setCompareMode((c) => !c)}
                    title="Compare all 3 models side by side"
                    style={{
                      height: 34,
                      borderRadius: 8,
                      cursor: "pointer",
                      background: compareMode ? t.accentDim : "transparent",
                      border: `1px solid ${compareMode ? t.accent : t.border1}`,
                      display: "flex",
                      alignItems: "center",
                      gap: 6,
                      padding: "0 10px",
                      fontFamily: fontFamily,
                      fontSize: 12,
                      color: compareMode ? t.accent : t.text3,
                      transition: "all .15s",
                    }}
                  >
                    <I.columns c={compareMode ? t.accent : t.text3} />
                    Compare
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
                    onClick={() => fileRef.current?.click()}
                    title="Add image"
                    style={{
                      width: 34,
                      height: 34,
                      borderRadius: 8,
                      cursor: "pointer",
                      background: image ? t.accentDim : "transparent",
                      border: `1px solid ${image ? t.accent : t.border1}`,
                      display: "flex",
                      alignItems: "center",
                      justifyContent: "center",
                      transition: "all .15s",
                    }}
                  >
                    <I.img c={image ? t.accent : t.text3} />
                  </button>
                </div>
                <button
                  onClick={handleSubmit}
                  disabled={!canSend}
                  style={{
                    width: 34,
                    height: 34,
                    borderRadius: 8,
                    cursor: canSend ? "pointer" : "not-allowed",
                    background: canSend ? t.accent : t.bgHover,
                    border: "none",
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "center",
                    transition: "background .15s",
                  }}
                >
                  <I.send on={!!canSend} c={canSend ? "#fff" : t.text4} />
                </button>
              </div>
            </div>
            <div
              style={{
                fontSize: 11,
                color: t.text4,
                textAlign: "center",
                marginTop: 6,
              }}
            >
              {compareMode
                ? "Compare mode — Enter sends to all 3 models"
                : "Enter to send · Shift+Enter for new line"}
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
      />
    </div>
  );
}
