/** Friendly display names with gray technical subtitles (current API ids preserved). */

const MODEL_LABELS_EN = {
  auto_rag: {
    friendly: "Smart mode",
    technical: "Auto (recommended) · auto_rag",
    description: "Picks the best source for your question automatically",
  },
  general_rag: {
    friendly: "Field guides",
    technical: "Agriculture Knowledge RAG · general_rag",
    description:
      "Crop care, soil, irrigation, and pest management from trusted references",
  },
  product_rag: {
    friendly: "Product lookup",
    technical: "Product Catalog RAG · product_rag",
    description: "Questions about company products, labels, and usage",
  },
  base_llm: {
    friendly: "General AI",
    technical: "Base LLM · base_llm",
    description: "Broad knowledge without your farm documents",
  },
  advisory: {
    friendly: "Full advisory",
    technical: "Advisory (General + Product) · advisory",
    description: "Field guidance first, then product suggestions when relevant",
  },
};

const MODEL_LABELS_AR = {
  auto_rag: {
    friendly: "الوضع الذكي",
    technical: "Auto (recommended) · auto_rag",
    description: "يختار أفضل مصدر للإجابة تلقائياً حسب سؤالك",
  },
  general_rag: {
    friendly: "إرشادات زراعية",
    technical: "Agriculture Knowledge RAG · general_rag",
    description:
      "نصائح للمحاصيل والتربة والري ومكافحة الآفات من مراجع موثوقة",
  },
  product_rag: {
    friendly: "منتجات الشركة",
    technical: "Product Catalog RAG · product_rag",
    description: "أسئلة عن منتجاتنا وبيانات الاستخدام والجرعات",
  },
  base_llm: {
    friendly: "ذكاء عام",
    technical: "Base LLM · base_llm",
    description: "معرفة عامة بدون مستنداتك الزراعية",
  },
  advisory: {
    friendly: "استشارة شاملة",
    technical: "Advisory (General + Product) · advisory",
    description: "إرشاد ميداني أولاً، ثم اقتراح منتجات عند الحاجة",
  },
};

export const ROUTED_LABELS_EN = {
  product_rag: "Product lookup",
  general_rag: "Field guides",
  base_llm: "General AI",
};

export const ROUTED_LABELS_AR = {
  product_rag: "منتجات الشركة",
  general_rag: "إرشادات زراعية",
  base_llm: "ذكاء عام",
};

export const ROUTED_TECHNICAL = {
  product_rag: "Product Catalog RAG · product_rag",
  general_rag: "Agriculture Knowledge RAG · general_rag",
  base_llm: "Base LLM · base_llm",
};

function labelsForLang(lang) {
  return lang === "ar" ? MODEL_LABELS_AR : MODEL_LABELS_EN;
}

function routedForLang(lang) {
  return lang === "ar" ? ROUTED_LABELS_AR : ROUTED_LABELS_EN;
}

export function getModelDisplay(
  id,
  { developerLabels = false, language = "en" } = {},
) {
  const row = labelsForLang(language)[id];
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

/** Localized description for picker — never fall back to English API strings in Arabic UI. */
export function getModelDescription(id, language = "en", apiDescription = "") {
  const labels = getModelDisplay(id, { language });
  if (labels.description) return labels.description;
  return language === "en" ? apiDescription : "";
}

export function getRoutedDisplay(
  routedTo,
  { developerLabels = false, language = "en" } = {},
) {
  if (!routedTo) return { friendly: "", technical: "", label: "" };
  const friendly = routedForLang(language)[routedTo] || routedTo;
  const technical = ROUTED_TECHNICAL[routedTo] || routedTo;
  return {
    friendly,
    technical,
    label: developerLabels ? technical : friendly,
  };
}

/** @deprecated use getModelDisplay with language */
export const MODEL_LABELS = MODEL_LABELS_EN;
export const ROUTED_LABELS = ROUTED_LABELS_EN;
