export const CLASSIC_DARK = {
  bg: "#0a0a0a",
  bgSide: "#111111",
  bgCard: "#1a1a1a",
  bgInput: "#1a1a1a",
  bgHover: "#222222",
  bgActive: "#2a2a2a",
  accent: "#10a37f",
  accentDim: "rgba(16,163,127,0.12)",
  text1: "#ececec",
  text2: "#c2c2c2",
  text3: "#a8a8a8",
  text4: "#909090",
  border1: "#2e2e2e",
  border2: "#222222",
  err: {
    bg: "rgba(220,80,60,0.09)",
    color: "#e07060",
    b: "rgba(220,80,60,0.22)",
  },
  btnText: "#ffffff",
  inputBorder: "#2e2e2e",
  inputFocus: "#10a37f",
  inputShadow: "rgba(16,163,127,0.15)",
  panelGeneral: null,
  panelProduct: null,
  confidenceBg: null,
  avatarRing: "rgba(16,163,127,0.2)",
};

export const CLASSIC_LIGHT = {
  bg: "#ffffff",
  bgSide: "#f7f7f8",
  bgCard: "#ffffff",
  bgInput: "#ffffff",
  bgHover: "#ececec",
  bgActive: "#e2e2e2",
  accent: "#10a37f",
  accentDim: "rgba(16,163,127,0.08)",
  text1: "#0d0d0d",
  text2: "#2d2d2d",
  text3: "#6b6b6b",
  text4: "#757575",
  border1: "#d9d9d9",
  border2: "#e8e8e8",
  err: { bg: "#fdecea", color: "#8b2820", b: "#f0b4b0" },
  btnText: "#ffffff",
  inputBorder: "#c0c0c0",
  inputFocus: "#10a37f",
  inputShadow: "rgba(16,163,127,0.18)",
  panelGeneral: null,
  panelProduct: null,
  confidenceBg: null,
  avatarRing: "rgba(16,163,127,0.15)",
};

export const CLASSIC_FONT =
  "'Segoe UI', system-ui, -apple-system, BlinkMacSystemFont, sans-serif";

export const CLASSIC_TM_CSS = `
@keyframes tm-fade-in{from{opacity:0}to{opacity:1}}
@keyframes tm-slide-up{from{opacity:0;transform:translateY(14px)}to{opacity:1;transform:translateY(0)}}
@keyframes tm-scale-in{from{opacity:0;transform:scale(.94) translateY(10px)}to{opacity:1;transform:scale(1) translateY(0)}}
@keyframes tm-logo-float{0%,100%{transform:translateY(0)}50%{transform:translateY(-5px)}}
@keyframes tm-spin{to{transform:rotate(360deg)}}

.tm-root{transition:background-color .3s ease}
.tm-shell{display:flex;flex:1;min-width:0;width:100%;height:100%;overflow:hidden;transition:filter .45s ease,transform .45s ease,opacity .45s ease}
.tm-gate-open .tm-shell{filter:blur(10px) saturate(.9);transform:scale(.982);opacity:.5;pointer-events:none}
.tm-app-ready .tm-shell{animation:tm-fade-in .55s ease}

.tm-gate-backdrop{animation:tm-fade-in .4s ease forwards}
.tm-gate-backdrop.tm-gate-exiting{animation:tm-fade-in .3s ease reverse forwards}
.tm-gate-modal{animation:tm-scale-in .5s cubic-bezier(.22,1,.36,1) forwards}
.tm-gate-backdrop.tm-gate-exiting .tm-gate-modal{animation:tm-scale-in .3s ease reverse forwards}

.tm-stagger-1{animation:tm-slide-up .5s cubic-bezier(.22,1,.36,1) .06s both}
.tm-stagger-2{animation:tm-slide-up .5s cubic-bezier(.22,1,.36,1) .12s both}
.tm-stagger-3{animation:tm-slide-up .5s cubic-bezier(.22,1,.36,1) .18s both}
.tm-stagger-4{animation:tm-slide-up .5s cubic-bezier(.22,1,.36,1) .24s both}
.tm-stagger-5{animation:tm-slide-up .5s cubic-bezier(.22,1,.36,1) .3s both}

.tm-gate-logo{animation:tm-logo-float 3.2s ease-in-out infinite}

.tm-privacy-collapse{display:grid;grid-template-rows:0fr;transition:grid-template-rows .3s cubic-bezier(.22,1,.36,1)}
.tm-privacy-collapse.tm-privacy-open{grid-template-rows:1fr}
.tm-privacy-inner{overflow:hidden;min-height:0}

.tm-gate-input{transition:border-color .2s ease,box-shadow .2s ease}
.tm-gate-input:focus{outline:none;border-color:#10a37f!important;box-shadow:0 0 0 3px rgba(16,163,127,.2)!important}

.tm-btn-primary{transition:transform .18s ease,opacity .18s ease,background .18s ease,box-shadow .18s ease}
.tm-btn-primary:not(:disabled):hover{transform:translateY(-1px);box-shadow:0 8px 24px rgba(16,163,127,.32)}
.tm-btn-primary:not(:disabled):active{transform:translateY(0);box-shadow:none}
.tm-btn-loading::after{content:"";width:14px;height:14px;margin-left:8px;border:2px solid rgba(255,255,255,.35);border-top-color:#fff;border-radius:50%;display:inline-block;vertical-align:-2px;animation:tm-spin .7s linear infinite}

.tm-empty-logo{animation:tm-scale-in .65s cubic-bezier(.22,1,.36,1) both}
.tm-empty-title{animation:tm-slide-up .55s cubic-bezier(.22,1,.36,1) .14s both}
.tm-empty-sub{animation:tm-slide-up .55s cubic-bezier(.22,1,.36,1) .22s both}
.tm-empty-chips{animation:tm-slide-up .55s cubic-bezier(.22,1,.36,1) .3s both}

.tm-chip{transition:transform .2s ease,background .15s ease,border-color .15s ease,box-shadow .2s ease}
.tm-chip:hover{transform:translateY(-2px);box-shadow:0 6px 16px rgba(0,0,0,.18)}

.tm-msg-in{animation:tm-slide-up .38s cubic-bezier(.22,1,.36,1) both}

.tm-composer{transition:border-color .25s ease,box-shadow .25s ease,transform .25s ease}
.tm-composer:focus-within{border-color:var(--tm-accent)!important;box-shadow:0 0 0 3px var(--tm-accent-dim),0 6px 24px rgba(0,0,0,.12)!important}

.tm-conv-item{transition:background .18s ease,border-color .15s,box-shadow .15s}

.tm-model-menu{animation:tm-scale-in .22s cubic-bezier(.22,1,.36,1) both;transform-origin:top right}
[dir=rtl] .tm-model-menu{transform-origin:top left}

.tm-icon-btn{transition:background .15s ease,transform .15s ease}
.tm-icon-btn:hover{transform:scale(1.06)}

@media (prefers-reduced-motion:reduce){
  *,*::before,*::after{animation:none!important;transition-duration:.01ms!important}
}
`;
