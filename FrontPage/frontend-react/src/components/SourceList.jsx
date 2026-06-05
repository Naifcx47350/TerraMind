import { useState } from "react";
import { sourceKind, relevanceLabel } from "../utils/displayHelpers.js";

function groupSources(sources) {
  const general = [];
  const product = [];
  for (const src of sources || []) {
    if (sourceKind(src) === "product") product.push(src);
    else general.push(src);
  }
  return { general, product };
}

function SourceRow({ src, t, ar }) {
  const rel = relevanceLabel(src.relevance_score);
  return (
    <div
      style={{
        padding: "8px 0",
        borderBottom: `1px solid ${t.border2}`,
        direction: ar ? "rtl" : "ltr",
        textAlign: ar ? "right" : "left",
      }}
    >
      <div
        style={{
          fontSize: 12,
          fontWeight: 600,
          color: t.text1,
          lineHeight: 1.4,
        }}
      >
        {src.title}
      </div>
      {src.section && (
        <div style={{ fontSize: 11, color: t.text3, marginTop: 2 }}>
          {src.section}
        </div>
      )}
      <div
        style={{
          fontSize: 10,
          color: t.text4,
          marginTop: 4,
          display: "flex",
          gap: 8,
          flexWrap: "wrap",
        }}
      >
        {rel && (
          <span>
            {ar ? "الصلة" : "Match"}: {rel}
          </span>
        )}
        {src.chunk_count > 1 && (
          <span>
            {src.chunk_count} {ar ? "مقاطع" : "chunks"}
          </span>
        )}
      </div>
    </div>
  );
}

function SourceGroup({ title, items, t, ar }) {
  if (!items.length) return null;
  return (
    <div style={{ marginBottom: 8 }}>
      <div
        style={{
          fontSize: 10,
          color: t.text4,
          textTransform: "uppercase",
          letterSpacing: "0.08em",
          marginBottom: 4,
        }}
      >
        {title}
      </div>
      {items.map((src, i) => (
        <SourceRow key={`${src.title}-${i}`} src={src} t={t} ar={ar} />
      ))}
    </div>
  );
}

export function SourceList({ sources, t, ar = false, appearance = "classic" }) {
  const [open, setOpen] = useState(false);
  const list = sources || [];
  if (!list.length) return null;

  const { general, product } = groupSources(list);
  const mixed = general.length > 0 && product.length > 0;
  const summaryParts = [];
  if (general.length)
    summaryParts.push(`${general.length} ${ar ? "مراجع" : "guides"}`);
  if (product.length)
    summaryParts.push(`${product.length} ${ar ? "منتجات" : "products"}`);

  return (
    <div
      style={{
        marginTop: 12,
        direction: ar ? "rtl" : "ltr",
        textAlign: ar ? "right" : "left",
      }}
    >
      <button
        type="button"
        onClick={() => setOpen((o) => !o)}
        style={{
          display: "flex",
          alignItems: "center",
          gap: 8,
          width: "100%",
          background: appearance === "field" ? t.confidenceBg || t.bgHover : t.bgCard,
          border: `1px solid ${t.border1}`,
          borderRadius: appearance === "field" ? 10 : 8,
          padding: "8px 12px",
          cursor: "pointer",
          fontFamily: "inherit",
          color: t.text2,
          fontSize: 12,
          textAlign: ar ? "right" : "left",
        }}
      >
        <span
          style={{
            width: 6,
            height: 6,
            borderRadius: "50%",
            background: t.accent,
            flexShrink: 0,
          }}
        />
        <span style={{ flex: 1 }}>
          {list.length} {ar ? "مصدر" : "source"}
          {list.length !== 1 ? (ar ? "" : "s") : ""}
          {mixed && ` · ${summaryParts.join(" · ")}`}
        </span>
        <span style={{ color: t.text4, fontSize: 10 }}>{open ? "▲" : "▼"}</span>
      </button>
      {open && (
        <div
          style={{
            marginTop: 6,
            padding: "4px 12px 8px",
            background: t.bgCard,
            border: `1px solid ${t.border1}`,
            borderRadius: appearance === "field" ? 10 : 8,
          }}
        >
          {mixed ? (
            <>
              <SourceGroup
                title={ar ? "مراجع عامة" : "Public references"}
                items={general}
                t={t}
                ar={ar}
              />
              <SourceGroup
                title={ar ? "\u0627\u0644\u0645\u0646\u062a\u062c\u0627\u062a" : "Product catalog"}
                items={product}
                t={t}
                ar={ar}
              />
            </>
          ) : (
            list.map((src, i) => (
              <SourceRow key={`${src.title}-${i}`} src={src} t={t} ar={ar} />
            ))
          )}
        </div>
      )}
    </div>
  );
}
