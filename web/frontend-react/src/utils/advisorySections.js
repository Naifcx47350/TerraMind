const SECTION_GENERAL =
  /###\s*Public agriculture guidance\s*\n*(.*?)(?=###\s*Company product catalog|\Z)/is;
const SECTION_PRODUCT = /###\s*Company product catalog\s*\n+(.*)\Z/is;

export function splitAdvisorySections(answer) {
  const text = (answer || "").trim();
  if (!text) {
    return { general: "", product: "", bothNonEmpty: false, hasSections: false };
  }

  const generalMatch = text.match(SECTION_GENERAL);
  const productMatch = text.match(SECTION_PRODUCT);
  const general = (generalMatch?.[1] || "").trim();
  const product = (productMatch?.[1] || "").trim();
  const hasSections = Boolean(generalMatch || productMatch);

  return {
    general,
    product,
    bothNonEmpty: Boolean(general && product),
    hasSections,
  };
}
