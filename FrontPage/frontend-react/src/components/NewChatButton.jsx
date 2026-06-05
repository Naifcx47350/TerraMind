export function NewChatButton({ onClick, t, label, fontFamily, rtl }) {
  return (
    <button
      type="button"
      className="tm-new-chat-btn"
      onClick={onClick}
      title={label}
      style={{
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        gap: 8,
        width: "100%",
        marginBottom: 12,
        padding: "10px 14px",
        background: t.accentDim,
        border: `1px solid ${t.accent}`,
        borderRadius: 10,
        color: t.accent,
        fontFamily: fontFamily,
        fontSize: 13,
        fontWeight: 600,
        cursor: "pointer",
        transition: "transform .15s ease, box-shadow .15s ease, background .15s",
        flexDirection: rtl ? "row-reverse" : "row",
      }}
      onMouseEnter={(e) => {
        e.currentTarget.style.transform = "translateY(-1px)";
        e.currentTarget.style.boxShadow = `0 4px 14px ${t.inputShadow}`;
      }}
      onMouseLeave={(e) => {
        e.currentTarget.style.transform = "translateY(0)";
        e.currentTarget.style.boxShadow = "none";
      }}
    >
      <svg
        width="16"
        height="16"
        viewBox="0 0 24 24"
        fill="none"
        stroke="currentColor"
        strokeWidth="2"
        strokeLinecap="round"
        strokeLinejoin="round"
        aria-hidden
      >
        <path d="M12 5v14M5 12h14" />
      </svg>
      {label}
    </button>
  );
}
