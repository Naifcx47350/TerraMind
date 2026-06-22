import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";

/**
 * Renders assistant answers as Markdown (headings, bold, lists, etc.).
 */
export function MarkdownMessage({ content, theme: t, dir = "ltr" }) {
  if (!content) return null;

  const align = dir === "rtl" ? "right" : "left";

  const components = {
    h1: ({ children }) => (
      <h1
        style={{
          fontSize: "calc(var(--tm-chat-font-size, 14px) * 1.43)",
          fontWeight: 700,
          color: t.text1,
          margin: "16px 0 8px",
          lineHeight: 1.3,
          textAlign: align,
        }}
      >
        {children}
      </h1>
    ),
    h2: ({ children }) => (
      <h2
        style={{
          fontSize: "calc(var(--tm-chat-font-size, 14px) * 1.21)",
          fontWeight: 700,
          color: t.text1,
          margin: "14px 0 6px",
          lineHeight: 1.35,
          textAlign: align,
        }}
      >
        {children}
      </h2>
    ),
    h3: ({ children }) => (
      <h3
        style={{
          fontSize: "calc(var(--tm-chat-font-size, 14px) * 1.07)",
          fontWeight: 600,
          color: t.text1,
          margin: "12px 0 4px",
          lineHeight: 1.4,
          textAlign: align,
        }}
      >
        {children}
      </h3>
    ),
    p: ({ children }) => (
      <p
        style={{
          margin: "0 0 10px",
          color: t.text2,
          lineHeight: 1.75,
          textAlign: align,
        }}
      >
        {children}
      </p>
    ),
    strong: ({ children }) => (
      <strong style={{ fontWeight: 700, color: t.text1 }}>{children}</strong>
    ),
    em: ({ children }) => (
      <em style={{ fontStyle: "italic", color: t.text2 }}>{children}</em>
    ),
    ul: ({ children }) => (
      <ul
        style={{
          margin: "0 0 12px",
          paddingLeft: dir === "rtl" ? 0 : 22,
          paddingRight: dir === "rtl" ? 22 : 0,
          color: t.text2,
          lineHeight: 1.7,
        }}
      >
        {children}
      </ul>
    ),
    ol: ({ children }) => (
      <ol
        style={{
          margin: "0 0 12px",
          paddingLeft: dir === "rtl" ? 0 : 22,
          paddingRight: dir === "rtl" ? 22 : 0,
          color: t.text2,
          lineHeight: 1.7,
        }}
      >
        {children}
      </ol>
    ),
    li: ({ children }) => (
      <li style={{ marginBottom: 4 }}>{children}</li>
    ),
    blockquote: ({ children }) => (
      <blockquote
        style={{
          margin: "0 0 12px",
          padding: "8px 12px",
          borderLeft:
            dir === "rtl"
              ? "none"
              : `3px solid ${t.accent}`,
          borderRight:
            dir === "rtl" ? `3px solid ${t.accent}` : "none",
          background: t.bgHover,
          borderRadius: 6,
          color: t.text3,
        }}
      >
        {children}
      </blockquote>
    ),
    code: ({ inline, children }) =>
      inline ? (
        <code
          style={{
            fontFamily: "Consolas, monospace",
            fontSize: "0.9em",
            background: t.bgHover,
            padding: "2px 6px",
            borderRadius: 4,
            color: t.text1,
          }}
        >
          {children}
        </code>
      ) : (
        <pre
          style={{
            margin: "0 0 12px",
            padding: 12,
            background: t.bgHover,
            borderRadius: 8,
            overflow: "auto",
            fontSize: "calc(var(--tm-chat-font-size, 14px) * 0.93)",
            lineHeight: 1.5,
          }}
        >
          <code style={{ fontFamily: "Consolas, monospace", color: t.text2 }}>
            {children}
          </code>
        </pre>
      ),
    hr: () => (
      <hr
        style={{
          border: "none",
          borderTop: `1px solid ${t.border1}`,
          margin: "16px 0",
        }}
      />
    ),
    a: ({ href, children }) => (
      <a
        href={href}
        target="_blank"
        rel="noopener noreferrer"
        style={{ color: t.accent, textDecoration: "underline" }}
      >
        {children}
      </a>
    ),
  };

  return (
    <div
      className="markdown-message"
      style={{
        direction: dir,
        wordBreak: "break-word",
        fontSize: "var(--tm-chat-font-size, 14px)",
      }}
    >
      <ReactMarkdown remarkPlugins={[remarkGfm]} components={components}>
        {content}
      </ReactMarkdown>
    </div>
  );
}
