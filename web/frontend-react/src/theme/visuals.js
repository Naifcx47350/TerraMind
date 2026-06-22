/**
 * Per-theme ambient backgrounds, logo tint, and decorative CSS.
 *
 * LOGO TUNING GUIDE
 * -----------------
 * File: web/frontend-react/src/theme/visuals.js
 *
 * All themes use the white PNG (`assets/logo/TM_Logo_white.png`) filled with
 * `logoTint` (defaults to theme accent from field.js / forest.js / etc.).
 *
 * `logoAvatarScale` — chat circle logo size multiplier (default 1.28 for all).
 * `logoFilter` — extra CSS filter on top of the tinted mask (usually "none").
 * `logoGlow` — drop-shadow glow (rgba string inside drop-shadow(...)).
 */

export const DEFAULT_LOGO_AVATAR_SCALE = 1.28;

export const THEME_VISUALS = {
  field: {
    logoVariant: "white",
    logoTint: "#10a37f",
    logoFilter: "none",
    logoAvatarScale: DEFAULT_LOGO_AVATAR_SCALE,
    logoGlow: "0 0 20px rgba(16,163,127,0.35)",
    ambientDark: `
      radial-gradient(ellipse 90% 55% at 50% -15%, rgba(16,163,127,0.14) 0%, transparent 55%),
      radial-gradient(ellipse 50% 40% at 95% 85%, rgba(16,163,127,0.07) 0%, transparent 50%),
      radial-gradient(ellipse 40% 35% at 5% 70%, rgba(16,163,127,0.05) 0%, transparent 45%)
    `,
    ambientLight: `
      radial-gradient(ellipse 90% 55% at 50% -10%, rgba(16,163,127,0.1) 0%, transparent 55%),
      radial-gradient(ellipse 50% 40% at 100% 90%, rgba(16,163,127,0.06) 0%, transparent 50%)
    `,
  },
  forest: {
    logoVariant: "white",
    logoTint: "#3d9b6a",
    logoFilter: "none",
    logoAvatarScale: DEFAULT_LOGO_AVATAR_SCALE,
    logoGlow: "0 0 22px rgba(61,155,106,0.4)",
    ambientDark: `
      radial-gradient(ellipse 85% 50% at 40% -10%, rgba(61,155,106,0.16) 0%, transparent 52%),
      radial-gradient(ellipse 45% 38% at 90% 80%, rgba(196,163,90,0.08) 0%, transparent 48%),
      radial-gradient(ellipse 35% 30% at 8% 60%, rgba(61,155,106,0.06) 0%, transparent 42%)
    `,
    ambientLight: `
      radial-gradient(ellipse 85% 50% at 45% -8%, rgba(45,122,82,0.12) 0%, transparent 52%),
      radial-gradient(ellipse 45% 38% at 95% 88%, rgba(168,132,46,0.07) 0%, transparent 48%)
    `,
  },
  harvest: {
    logoVariant: "white",
    logoTint: "#d4a017",
    logoFilter: "none",
    logoAvatarScale: DEFAULT_LOGO_AVATAR_SCALE,
    logoGlow: "0 0 24px rgba(212,160,23,0.45)",
    ambientDark: `
      radial-gradient(ellipse 88% 52% at 50% -12%, rgba(212,160,23,0.15) 0%, transparent 54%),
      radial-gradient(ellipse 48% 42% at 92% 78%, rgba(232,197,71,0.09) 0%, transparent 50%),
      radial-gradient(ellipse 38% 32% at 10% 65%, rgba(139,105,20,0.07) 0%, transparent 44%)
    `,
    ambientLight: `
      radial-gradient(ellipse 88% 52% at 48% -8%, rgba(184,134,11,0.12) 0%, transparent 54%),
      radial-gradient(ellipse 48% 42% at 98% 85%, rgba(212,160,23,0.08) 0%, transparent 50%)
    `,
  },
  ocean: {
    logoVariant: "white",
    logoTint: "#3a9ec4",
    logoFilter: "none",
    logoAvatarScale: DEFAULT_LOGO_AVATAR_SCALE,
    logoGlow: "0 0 24px rgba(58,158,196,0.42)",
    ambientDark: `
      radial-gradient(ellipse 90% 55% at 55% -14%, rgba(58,158,196,0.16) 0%, transparent 54%),
      radial-gradient(ellipse 50% 40% at 8% 75%, rgba(90,158,196,0.08) 0%, transparent 48%),
      radial-gradient(ellipse 42% 35% at 95% 40%, rgba(42,106,138,0.06) 0%, transparent 45%)
    `,
    ambientLight: `
      radial-gradient(ellipse 90% 55% at 50% -10%, rgba(42,122,158,0.11) 0%, transparent 54%),
      radial-gradient(ellipse 50% 40% at 5% 80%, rgba(74,158,196,0.07) 0%, transparent 48%)
    `,
  },
  dusk: {
    logoVariant: "white",
    logoTint: "#9b7ed4",
    logoFilter: "none",
    logoAvatarScale: DEFAULT_LOGO_AVATAR_SCALE,
    logoGlow: "0 0 24px rgba(155,126,212,0.4)",
    ambientDark: `
      radial-gradient(ellipse 88% 54% at 45% -12%, rgba(155,126,212,0.15) 0%, transparent 54%),
      radial-gradient(ellipse 46% 38% at 88% 82%, rgba(196,168,232,0.08) 0%, transparent 48%),
      radial-gradient(ellipse 36% 30% at 12% 55%, rgba(106,80,144,0.07) 0%, transparent 44%)
    `,
    ambientLight: `
      radial-gradient(ellipse 88% 54% at 50% -8%, rgba(122,90,184,0.11) 0%, transparent 54%),
      radial-gradient(ellipse 46% 38% at 92% 88%, rgba(155,126,212,0.07) 0%, transparent 48%)
    `,
  },
};

export const DECORATIVE_CSS = `
.tm-ambient-layer{
  position:fixed;inset:0;pointer-events:none;z-index:0;
  transition:background .5s ease;
}
.tm-ambient-layer::after{
  content:"";position:absolute;inset:0;opacity:.035;
  background-image:radial-gradient(rgba(255,255,255,0.55) 0.6px,transparent 0.6px);
  background-size:18px 18px;
}
.tm-shell{position:relative;z-index:1}
.tm-empty-logo-wrap{
  position:relative;display:inline-block;
  padding:12px;border-radius:50%;
  background:radial-gradient(circle,rgba(var(--tm-accent-rgb,16,163,127),0.12) 0%,transparent 70%);
  box-shadow:0 0 40px rgba(var(--tm-accent-rgb,16,163,127),0.15);
}
.tm-empty-logo-wrap .tm-logo-mask{
  filter:var(--tm-logo-filter,none);
}
.tm-logo-mask{
  transition:filter .4s ease,background-color .4s ease;
}
.tm-chip{
  backdrop-filter:blur(8px);
  border:1px solid rgba(255,255,255,0.06)!important;
  box-shadow:0 1px 0 rgba(255,255,255,0.04),inset 0 1px 0 rgba(255,255,255,0.03);
}
.tm-composer{
  position:relative;
  backdrop-filter:blur(12px);
  background:color-mix(in srgb,var(--tm-bg-input,#1a1a1a) 88%,transparent)!important;
  box-shadow:0 8px 32px rgba(0,0,0,0.18),inset 0 1px 0 rgba(255,255,255,0.04);
  transition:border-color .4s ease,box-shadow .4s ease,background .35s ease;
}
.tm-composer--compare{
  box-shadow:0 10px 36px rgba(0,0,0,0.22),0 0 0 1px color-mix(in srgb,var(--tm-accent) 22%,transparent),inset 0 1px 0 rgba(255,255,255,0.05)!important;
}
.tm-composer--drag{
  border-color:var(--tm-accent)!important;
  box-shadow:0 0 0 1px color-mix(in srgb,var(--tm-accent) 28%,transparent),0 12px 36px rgba(0,0,0,0.22)!important;
}
.tm-composer-drop-overlay{
  position:absolute;
  inset:0;
  z-index:3;
  display:flex;
  align-items:center;
  justify-content:center;
  border-radius:inherit;
  background:color-mix(in srgb,var(--tm-bg-input,#1a1a1a) 72%,transparent);
  border:2px dashed color-mix(in srgb,var(--tm-accent) 65%,transparent);
  color:var(--tm-accent);
  font-size:13px;
  font-weight:600;
  pointer-events:none;
  backdrop-filter:blur(8px);
}
.tm-composer-attachment{
  display:flex;
  align-items:center;
  gap:10px;
  padding:8px 10px;
  margin-bottom:2px;
  background:color-mix(in srgb,var(--tm-bg,#0a0a0a) 55%,transparent);
  border:1px solid var(--tm-border1,rgba(255,255,255,0.08));
  border-radius:10px;
}
.tm-composer-attachment-thumb{
  width:44px;
  height:44px;
  object-fit:cover;
  border-radius:8px;
  border:1px solid var(--tm-border1,rgba(255,255,255,0.08));
  flex-shrink:0;
}
.tm-composer-attachment-name{
  font-size:13px;
  white-space:nowrap;
  overflow:hidden;
  text-overflow:ellipsis;
}
.tm-composer-attachment-meta{font-size:11px}
.tm-composer-attachment-remove{
  background:transparent;
  border:none;
  cursor:pointer;
  padding:4px;
  font-size:16px;
  line-height:1;
  flex-shrink:0;
}
.tm-root.tm-stylized .tm-ambient-layer{
  background-size:cover,cover!important;
  background-position:center center,center bottom!important;
  background-repeat:no-repeat,no-repeat!important;
}
.tm-root.tm-stylized .tm-ambient-layer::before{
  content:"";
  position:absolute;
  inset:0;
  background:linear-gradient(180deg,rgba(0,0,0,0.22) 0%,rgba(0,0,0,0.08) 45%,rgba(0,0,0,0.28) 100%);
  pointer-events:none;
}
.tm-root.tm-stylized.tm-light .tm-ambient-layer::before{
  background:linear-gradient(180deg,rgba(255,255,255,0.4) 0%,rgba(255,255,255,0.15) 45%,rgba(255,255,255,0.5) 100%);
}
.tm-input-footer--stylized{
  background:transparent!important;
}
.tm-topbar--stylized{
  background:color-mix(in srgb,var(--tm-bg,#0a0a0a) 55%,transparent)!important;
}
.tm-profile-avatar-wrap{
  position:relative;
  width:32px;
  height:32px;
  flex-shrink:0;
  overflow:visible;
}
.tm-profile-decor{
  z-index:2;
}
.tm-composer-wrap{
  position:relative;
  overflow:visible;
  isolation:isolate;
}
.tm-decor-fixed{
  flex-shrink:0;
  image-rendering:auto;
}
.tm-composer--stylized{
  position:relative;
  z-index:1;
  background:color-mix(in srgb,var(--tm-bg-input,#1a1a1a) 72%,transparent)!important;
  backdrop-filter:blur(14px) saturate(1.1);
}
.tm-advanced-panel{
  animation:tm-scale-in .22s cubic-bezier(.22,1,.36,1) both;
}
.tm-advanced-toggle:hover{
  background:color-mix(in srgb,var(--tm-bg-hover,#222) 80%,transparent);
}
.tm-composer-decor{
  z-index:3;
  pointer-events:none;
}
.tm-decor-img{
  mix-blend-mode:screen;
  opacity:1;
  filter:drop-shadow(0 0 14px color-mix(in srgb,var(--tm-accent) 45%,transparent));
}
.tm-root.tm-light .tm-decor-img{
  mix-blend-mode:multiply;
  filter:drop-shadow(0 2px 8px rgba(0,0,0,0.18));
}
.tm-root.tm-light .tm-composer-decor.tm-decor-img{
  mix-blend-mode:normal;
  filter:drop-shadow(0 2px 10px rgba(0,0,0,0.12));
}
.tm-welcome-card-decor.tm-decor-img{
  mix-blend-mode:screen;
}
.tm-stylized .tm-content-width{
  position:relative;
}
.tm-stylized:not(.tm-light) .tm-content-width::before{
  content:"";
  position:absolute;
  inset:-20px -12px;
  pointer-events:none;
  z-index:-1;
  border-radius:18px;
  background:radial-gradient(ellipse at center,rgba(0,0,0,0.38) 0%,rgba(0,0,0,0.14) 55%,transparent 100%);
}
.tm-stylized.tm-light .tm-content-width::before{
  content:"";
  position:absolute;
  inset:-20px -12px;
  pointer-events:none;
  z-index:-1;
  border-radius:18px;
  background:radial-gradient(ellipse at center,rgba(255,255,255,0.72) 0%,rgba(255,255,255,0.35) 55%,transparent 100%);
}
.tm-stylized:not(.tm-light) .markdown-message p,
.tm-stylized:not(.tm-light) .markdown-message li,
.tm-stylized:not(.tm-light) .markdown-message ol,
.tm-stylized:not(.tm-light) .markdown-message ul{
  text-shadow:0 1px 2px rgba(0,0,0,0.45);
}
.tm-stylized.tm-light .markdown-message p,
.tm-stylized.tm-light .markdown-message li,
.tm-stylized.tm-light .markdown-message ol,
.tm-stylized.tm-light .markdown-message ul{
  text-shadow:0 0 1px rgba(255,255,255,0.95),0 1px 2px rgba(255,255,255,0.8);
}
.tm-stylized .tm-msg-meta{
  text-shadow:0 1px 2px rgba(0,0,0,0.35);
}
.tm-stylized.tm-light .tm-msg-meta{
  text-shadow:0 0 1px rgba(255,255,255,0.9);
}
.tm-layout-toggle{
  display:flex;
  gap:3px;
  padding:3px;
  margin-bottom:6px;
  border-radius:11px;
  border:1px solid var(--tm-border1,rgba(255,255,255,0.08));
  background:color-mix(in srgb,var(--tm-bg-input,#1a1a1a) 70%,transparent);
}
.tm-layout-toggle-btn{
  flex:1;
  display:flex;
  flex-direction:column;
  align-items:center;
  gap:2px;
  padding:8px 6px;
  border-radius:8px;
  border:1px solid transparent;
  background:transparent;
  cursor:pointer;
  font-family:inherit;
  transition:background .2s ease,border-color .2s ease,box-shadow .2s ease,color .2s ease;
}
.tm-layout-toggle-btn--active{
  background:color-mix(in srgb,var(--tm-accent-dim) 90%,transparent);
  border-color:color-mix(in srgb,var(--tm-accent) 45%,transparent);
  box-shadow:0 0 16px color-mix(in srgb,var(--tm-accent) 18%,transparent),inset 0 1px 0 rgba(255,255,255,0.06);
}
.tm-layout-toggle-icon{
  font-size:15px;
  line-height:1;
}
.tm-layout-toggle-label{
  font-size:11px;
  font-weight:600;
  letter-spacing:0.02em;
}
.tm-layout-toggle-hint{
  font-size:10px;
  line-height:1.35;
  margin-bottom:14px;
  text-align:center;
  color:var(--tm-text3,#888);
}
.tm-welcome-card{
  animation:tm-scale-in .35s cubic-bezier(.22,1,.36,1) both;
}
.tm-composer-btn{
  position:relative;
  display:inline-flex;
  align-items:center;
  justify-content:center;
  gap:6px;
  height:34px;
  padding:0 11px;
  border-radius:10px;
  border:1px solid var(--tm-border1,rgba(255,255,255,0.08));
  background:color-mix(in srgb,var(--tm-bg-input,#1a1a1a) 55%,transparent);
  font-size:12px;
  cursor:pointer;
  transition:background .2s ease,border-color .2s ease,box-shadow .2s ease,transform .15s ease,color .2s ease;
}
.tm-composer-btn--icon{width:34px;padding:0}
.tm-composer-btn:hover{
  background:color-mix(in srgb,var(--tm-accent-dim) 85%,transparent);
  border-color:color-mix(in srgb,var(--tm-accent) 35%,transparent);
  transform:translateY(-1px);
}
.tm-composer-btn--active{
  background:var(--tm-accent-dim);
  border-color:var(--tm-accent);
  box-shadow:0 0 0 1px color-mix(in srgb,var(--tm-accent) 18%,transparent),0 4px 14px rgba(0,0,0,0.12);
}
.tm-composer-btn--active::after{
  content:"";
  position:absolute;
  top:5px;
  inset-inline-end:5px;
  width:6px;
  height:6px;
  border-radius:50%;
  background:var(--tm-accent);
  box-shadow:0 0 8px var(--tm-accent);
}
.tm-composer-btn--compare.tm-composer-btn--active{
  animation:tm-compare-pulse 2.4s ease-in-out infinite;
}
@keyframes tm-compare-pulse{
  0%,100%{box-shadow:0 0 0 1px color-mix(in srgb,var(--tm-accent) 18%,transparent),0 4px 14px rgba(0,0,0,0.12)}
  50%{box-shadow:0 0 0 1px color-mix(in srgb,var(--tm-accent) 35%,transparent),0 0 18px color-mix(in srgb,var(--tm-accent) 25%,transparent)}
}
.tm-composer-send{
  width:34px;
  height:34px;
  border-radius:10px;
  border:none;
  display:flex;
  align-items:center;
  justify-content:center;
  transition:background .2s ease,box-shadow .25s ease,transform .15s ease;
}
.tm-composer-send--ready{
  box-shadow:0 0 18px color-mix(in srgb,var(--tm-accent) 42%,transparent);
}
.tm-composer-send--ready:hover{transform:translateY(-1px) scale(1.04)}
.tm-voice-control{
  position:relative;
  display:flex;
  align-items:center;
}
.tm-voice-trigger{
  height:34px;
  width:38px;
  padding:0;
  border-radius:10px;
  border:1px solid var(--tm-border1,rgba(255,255,255,0.08));
  background:color-mix(in srgb,var(--tm-bg-input,#1a1a1a) 55%,transparent);
  display:inline-flex;
  align-items:center;
  justify-content:center;
  gap:4px;
  cursor:pointer;
  overflow:hidden;
  transition:width .2s ease,background .2s ease,border-color .2s ease,box-shadow .2s ease,transform .15s ease;
}
.tm-voice-trigger svg{
  flex:0 0 auto;
}
.tm-voice-control:hover .tm-voice-trigger,
.tm-voice-control--open .tm-voice-trigger,
.tm-voice-trigger:focus-visible{
  width:54px;
  background:color-mix(in srgb,var(--tm-accent-dim) 80%,transparent);
  border-color:color-mix(in srgb,var(--tm-accent) 42%,transparent);
}
.tm-voice-trigger:hover{transform:translateY(-1px)}
.tm-voice-trigger--active{
  border-color:var(--tm-accent)!important;
  box-shadow:0 0 0 1px color-mix(in srgb,var(--tm-accent) 45%,transparent),0 0 22px color-mix(in srgb,var(--tm-accent) 48%,transparent);
  animation:tm-voice-listening 1.2s ease-in-out infinite;
}
@keyframes tm-voice-listening{
  0%,100%{transform:translateY(0) scale(1)}
  50%{transform:translateY(-1px) scale(1.04)}
}
.tm-voice-trigger-arrow{
  display:inline-flex;
  align-items:center;
  justify-content:center;
  width:0;
  max-width:0;
  overflow:hidden;
  font-size:15px;
  line-height:1;
  opacity:0;
  transform:translateX(-3px);
  transition:opacity .18s ease,transform .18s ease,width .18s ease,max-width .18s ease;
}
.tm-voice-control:hover .tm-voice-trigger-arrow,
.tm-voice-control--open .tm-voice-trigger-arrow{
  width:13px;
  max-width:13px;
  opacity:.9;
  transform:translateX(0);
}
.tm-voice-menu{
  position:absolute;
  inset-inline-end:0;
  bottom:calc(100% + 8px);
  z-index:250;
  width:min(320px,calc(100vw - 32px));
  border:1px solid;
  border-radius:14px;
  padding:8px;
  box-shadow:0 18px 48px rgba(0,0,0,.36),inset 0 1px 0 rgba(255,255,255,.05);
  backdrop-filter:blur(16px) saturate(1.18);
  animation:tm-voice-pop .16s cubic-bezier(.22,1,.36,1) both;
  transform-origin:bottom right;
}
.tm-voice-menu::after{
  content:"";
  position:absolute;
  inset-inline:0;
  bottom:-10px;
  height:10px;
}
[dir=rtl] .tm-voice-menu{transform-origin:bottom left}
@keyframes tm-voice-pop{
  from{opacity:0;transform:translateY(6px) scale(.98)}
  to{opacity:1;transform:translateY(0) scale(1)}
}
.tm-voice-meter-row{
  display:flex;
  align-items:center;
  gap:10px;
  padding:6px 8px 8px;
}
.tm-voice-meter{
  height:7px;
  flex:1;
  border-radius:999px;
  overflow:hidden;
}
.tm-voice-live{
  font-size:11px;
  font-weight:700;
  white-space:nowrap;
}
.tm-voice-meter-fill{
  height:100%;
  border-radius:999px;
  transition:width 75ms ease-out;
}
.tm-voice-section-label{
  padding:3px 8px 5px;
  font-size:11px;
  font-weight:600;
}
.tm-voice-device-list{
  max-height:160px;
  overflow:auto;
}
.tm-voice-device{
  width:100%;
  border:0;
  border-radius:9px;
  background:transparent;
  display:flex;
  align-items:center;
  justify-content:space-between;
  gap:10px;
  padding:8px;
  font:inherit;
  font-size:13px;
  text-align:start;
  cursor:pointer;
}
.tm-voice-device:hover{
  background:color-mix(in srgb,var(--tm-accent-dim) 72%,transparent);
}
.tm-voice-device span:first-child{
  min-width:0;
  overflow:hidden;
  text-overflow:ellipsis;
  white-space:nowrap;
}
.tm-voice-empty,
.tm-voice-error,
.tm-voice-interim{
  padding:7px 8px;
  font-size:12px;
  line-height:1.4;
}
.tm-voice-interim{
  font-style:italic;
}
.tm-voice-hold-row{
  width:100%;
  border:0;
  border-top:1px solid;
  background:transparent;
  margin-top:6px;
  padding:10px 8px 4px;
  display:flex;
  align-items:center;
  justify-content:space-between;
  gap:12px;
  font:inherit;
  font-size:13px;
  cursor:pointer;
}
.tm-voice-switch{
  width:38px;
  height:22px;
  border-radius:999px;
  padding:2px;
  display:inline-flex;
  justify-content:flex-start;
  transition:background .2s ease;
}
.tm-voice-switch span{
  width:18px;
  height:18px;
  border-radius:50%;
  background:#fff;
  box-shadow:0 1px 4px rgba(0,0,0,.25);
  transition:transform .2s cubic-bezier(.22,1,.36,1);
}
.tm-voice-switch--on span{
  transform:translateX(16px);
}
[dir=rtl] .tm-voice-switch--on span{
  transform:translateX(-16px);
}
.tm-content-width{
  max-width:720px;
  width:100%;
  transition:max-width .48s cubic-bezier(0.34,1.12,0.64,1);
  will-change:max-width;
}
.tm-content-width--chat:not(.tm-content-width--wide){max-width:820px}
.tm-content-width--composer:not(.tm-content-width--wide){max-width:820px}
.tm-content-width--wide{max-width:min(100%,1280px)}
.tm-sidebar-glass{
  backdrop-filter:blur(16px) saturate(1.2);
}
.tm-topbar-glass{
  backdrop-filter:blur(12px) saturate(1.15);
  background:color-mix(in srgb,var(--tm-bg,#0a0a0a) 82%,transparent)!important;
  box-shadow:0 1px 0 rgba(255,255,255,0.04);
}
.tm-topbar{
  display:flex;
  align-items:flex-start;
  justify-content:space-between;
  gap:12px;
  padding:8px 16px;
  min-height:50px;
  min-width:0;
  overflow:visible;
}
.tm-topbar-start{
  display:flex;
  align-items:center;
  gap:10px;
  min-width:0;
  flex:1 1 0;
  overflow:hidden;
  padding-top:3px;
}
.tm-topbar-brand-text{
  white-space:nowrap;
  overflow:hidden;
  text-overflow:ellipsis;
  min-width:0;
}
.tm-topbar-end{
  flex:0 0 auto;
  max-width:min(200px,calc(100vw - 120px));
  min-width:0;
  display:flex;
  flex-direction:column;
  align-items:flex-end;
  gap:2px;
  position:relative;
  padding-top:3px;
}
.tm-model-trigger{
  display:inline-flex;
  align-items:center;
  gap:6px;
  width:auto;
  max-width:100%;
  min-width:0;
  border-radius:10px;
  padding:6px 10px;
  font-size:13px;
  font-weight:600;
  transition:border-color .15s,background .15s,box-shadow .15s;
  flex-shrink:0;
}
.tm-model-trigger-label{
  max-width:min(168px,calc(100vw - 130px));
  overflow:hidden;
  text-overflow:ellipsis;
  white-space:nowrap;
  text-align:start;
}
.tm-auto-route-hint{
  font-size:10px;
  line-height:1.35;
  max-width:100%;
  min-width:0;
}
.tm-auto-route-hint-main{
  display:block;
  overflow:hidden;
  text-overflow:ellipsis;
  white-space:nowrap;
}
.tm-auto-route-hint-tech{
  margin-top:1px;
  overflow:hidden;
  text-overflow:ellipsis;
  white-space:nowrap;
  direction:ltr;
  unicode-bidi:isolate;
}
.tm-model-menu{
  position:absolute;
  top:calc(100% + 6px);
  inset-inline-end:0;
  inset-inline-start:auto;
  width:max-content;
  min-width:248px;
  max-width:min(300px,calc(100vw - 16px));
  border-radius:12px;
  padding:4px;
  backdrop-filter:blur(16px) saturate(1.2);
  max-height:min(320px,calc(100vh - 88px));
  overflow-y:auto;
  overflow-x:hidden;
  overscroll-behavior:contain;
  z-index:200!important;
  box-shadow:0 12px 40px rgba(0,0,0,0.35),inset 0 1px 0 rgba(255,255,255,0.05);
  transform-origin:top right;
}
[dir=rtl] .tm-model-menu{transform-origin:top left}
.tm-model-menu-item{
  box-sizing:border-box;
}
.tm-model-menu-item-tech{
  font-size:10px;
  line-height:1.35;
  margin-top:2px;
  direction:ltr;
  unicode-bidi:isolate;
  white-space:normal;
  word-break:break-word;
}
@media (max-width:720px){
  .tm-topbar-brand-text{display:none}
  .tm-topbar-end{max-width:min(180px,calc(100vw - 96px))}
  .tm-model-menu{
    min-width:220px;
    max-width:min(280px,calc(100vw - 16px));
  }
}
@media (max-width:480px){
  .tm-composer-btn--compare .tm-composer-btn-label{display:none}
  .tm-composer-btn--compare{padding:0;width:34px}
}
.tm-model-menu-item-desc{
  display:-webkit-box;
  -webkit-line-clamp:2;
  -webkit-box-orient:vertical;
  overflow:hidden;
}
.tm-chip-dot::before{
  content:"";width:5px;height:5px;border-radius:50%;
  background:var(--tm-accent);display:inline-block;margin-inline-end:6px;
  vertical-align:middle;opacity:.85;
}
.tm-conv-item{
  border:1px solid transparent;
  transition:border-color .15s,background .15s,box-shadow .15s;
}
.tm-conv-item:hover{
  border-color:rgba(var(--tm-accent-rgb,16,163,127),0.12);
  box-shadow:0 2px 12px rgba(0,0,0,0.08);
}
`;
