/** Friendly display names with gray technical subtitles (current API ids preserved). */

export const MODEL_LABELS = {
  auto_rag: {
    friendly: "Smart mode",
    technical: "Auto (recommended) · auto_rag",
    description:
      "Picks Product Catalog or Agriculture Knowledge RAG from your question",
  },
  general_rag: {
    friendly: "Field and IPM guides",
    technical: "Agriculture Knowledge RAG · general_rag",
    description:
      "Public refs: GAP, soil health, rotation, IPM — not product catalog",
  },
  product_rag: {
    friendly: "Product catalog",
    technical: "Product Catalog RAG · product_rag",
    description: "Client Excel product sheets",
  },
  base_llm: {
    friendly: "General AI (no documents)",
    technical: "Base LLM · base_llm",
    description: "OpenAI only — no retrieval (comparison baseline)",
  },
  advisory: {
    friendly: "Advisory (both layers)",
    technical: "Advisory (General + Product) · advisory",
    description: "IPM guidance from public refs, then catalog products",
  },
};

export const ROUTED_LABELS = {
  product_rag: "Product catalog",
  general_rag: "Field and IPM guides",
  base_llm: "General AI (no documents)",
};

export const ROUTED_TECHNICAL = {
  product_rag: "Product Catalog RAG · product_rag",
  general_rag: "Agriculture Knowledge RAG · general_rag",
  base_llm: "Base LLM · base_llm",
};

export function getModelDisplay(id, { developerLabels = false } = {}) {
  const row = MODEL_LABELS[id];
  if (!row) {
    return {
      friendly: id,
      technical: id,
      description: "",
      pickerTitle: id,
    };
  }
  return {
    ...row,
    pickerTitle: developerLabels ? row.technical : row.friendly,
  };
}

export function getRoutedDisplay(routedTo, { developerLabels = false } = {}) {
  if (!routedTo) return { friendly: "", technical: "" };
  return {
    friendly: ROUTED_LABELS[routedTo] || routedTo,
    technical: ROUTED_TECHNICAL[routedTo] || routedTo,
    label: developerLabels
      ? ROUTED_TECHNICAL[routedTo] || routedTo
      : ROUTED_LABELS[routedTo] || routedTo,
  };
}
