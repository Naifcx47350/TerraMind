"""General RAG — paths and model settings."""

from pathlib import Path

from dotenv import load_dotenv
from langchain_core.prompts import ChatPromptTemplate

load_dotenv()

REPO_ROOT = Path(__file__).resolve().parents[3]

GENERAL_DOCUMENTS_DIR = REPO_ROOT / "data/raw/documents"
GENERAL_TEXT_DIR = REPO_ROOT / "data/raw/text"
GENERAL_SAMPLE_DIR = REPO_ROOT / "data/sample"
EVAL_QUESTIONS_PATH = REPO_ROOT / "data/eval/general_rag_questions.json"

CHROMA_PATH = REPO_ROOT / "vectorstore" / "chroma"

TEXT_EXTENSIONS = {".md", ".markdown", ".txt"}
PDF_EXTENSIONS = {".pdf"}
SUPPORTED_EXTENSIONS = TEXT_EXTENSIONS | PDF_EXTENSIONS

# Safety net: ignore this name if re-added (canonical FAO source is Pest_Mangment_FAO.pdf).
EXCLUDED_FILENAMES: frozenset[str] = frozenset(
    {
        "Pest_Management_FAO.md",
    }
)

# corpus_topic values used in metadata and retrieval boosting
CORPUS_TOPICS = frozenset(
    {"ipm", "soil", "gap", "fungicide", "pesticide_policy", "safety"}
)

DOCUMENT_DISPLAY_NAMES: dict[str, str] = {
    "2020-Guide-to-Integrated-Pest-Management.pdf": (
        "Guide to Integrated Pest Management (Univ. of Minnesota, 2020)"
    ),
    "Building-Soils-for-Better-Crops.pdf": (
        "Building Soils for Better Crops — Ecological Soil Management (4th ed.)"
    ),
    "fungicideefficacytiming.pdf": (
        "Fungicides & Bactericides: Efficacy & Timing (UC Fruit & Nut Crops)"
    ),
    "Managing pesticides in agriculture and public health.pdf": (
        "FAO/WHO International Code of Conduct on Pesticide Management"
    ),
    "Pest_Mangment_FAO.pdf": (
        "FAO IPM Guidance for Major Crop Pests & Diseases (2025)"
    ),
    "Training manual(GAP).pdf": (
        "FAO Good Agricultural Practices (GAP) Training Manual"
    ),
    "pesticide_safety_general.txt": (
        "General Pesticide Safety Guidelines"
    ),
}

# Single source of truth: filename -> topic tag
FILENAME_TO_TOPIC: dict[str, str] = {
    "2020-Guide-to-Integrated-Pest-Management.pdf": "ipm",
    "Pest_Mangment_FAO.pdf": "ipm",
    "Building-Soils-for-Better-Crops.pdf": "soil",
    "Training manual(GAP).pdf": "gap",
    "fungicideefficacytiming.pdf": "fungicide",
    "Managing pesticides in agriculture and public health.pdf": "pesticide_policy",
    "pesticide_safety_general.txt": "safety",
}

# Keyword hints for topic-aware retrieval (query -> topic)
TOPIC_QUERY_KEYWORDS: dict[str, tuple[str, ...]] = {
    "soil": (
        "soil",
        "organic matter",
        "tillage",
        "cover crop",
        "compost",
        "nutrient",
        "building soils",
    ),
    "gap": ("gap", "good agricultural", "traceability", "record keeping", "food safety"),
    "fungicide": (
        "fungicide",
        "bactericide",
        "efficacy",
        "timing",
        "spray timing",
        "fruit tree",
    ),
    "pesticide_policy": (
        "code of conduct",
        "stewardship",
        "public health",
        "who",
        "fao code",
        "pesticide management",
    ),
    "safety": (
        "ppe",
        "label",
        "sds",
        "mixing",
        "re-entry",
        "safety",
        "rinse",
    ),
    "ipm": (
        "ipm",
        "integrated pest",
        "late blight",
        "pest",
        "disease",
        "biological control",
        "monitoring",
        "threshold",
        "rotation",
        "sanitation",
    ),
}

INSPECT_MIN_CHARS = 5_000
INSPECT_MIN_CHARS_TEXT = 400
INSPECT_PREVIEW_CHARS = 500

# Only these basenames are ingested from data/sample/ (avoids stray demo product snippets).
SAMPLE_FILE_ALLOWLIST: frozenset[str] = frozenset(
    {"pesticide_safety_general.txt"}
)

GENERAL_RAG_INTRO = (
    "The General Agriculture RAG is built from trusted public agriculture references "
    "covering good agricultural practices, soil health, cover crops, crop rotation, and "
    "integrated pest management. This gives TerraMind a broader knowledge layer, while "
    "the Product RAG remains responsible for company-specific product information."
)

EMBEDDING_MODEL = "text-embedding-3-small"
CHAT_MODEL = "gpt-4o-mini"

CHUNK_SIZE = 1200
CHUNK_OVERLAP = 200
MARKDOWN_HEADERS = [("#", "h1"), ("##", "h2"), ("###", "h3")]

RETRIEVAL_K = 6
RETRIEVAL_FETCH_K = 24
MMR_LAMBDA = 0.65
TOPIC_BOOST_FETCH_MULTIPLIER = 2
HYBRID_LEXICAL_WEIGHT = 0.25


def display_name_for_file(filename: str) -> str | None:
    return DOCUMENT_DISPLAY_NAMES.get(filename)


def topic_for_filename(filename: str) -> str:
    return FILENAME_TO_TOPIC.get(filename, "ipm")


def document_id_for_path(path: Path) -> str:
    return path.stem


RAG_PROMPT = ChatPromptTemplate.from_template(
    """You are TerraMind General Agriculture Advisor — a practical assistant for farmers,
growers, and agronomists. Your knowledge layer draws on trusted public references on
good agricultural practices (GAP), soil health, cover crops, crop rotation, integrated
pest management (IPM), pesticide stewardship, and crop protection principles.
You are NOT the product catalog mode: do not recommend specific commercial products,
trade names, SKUs, or label-exact dosages unless they appear in the excerpts below.

Retrieved knowledge base excerpts (each block starts with a source label in brackets):
{document}

User question:
{question}

How to answer:
1. Use the excerpts as your primary source when they apply — paraphrase and organize
   what they say; prefer their facts over generic filler.
2. When stating important facts from the excerpts, cite the source label shown in brackets
   once per major point, e.g. (FAO IPM Guidance 2025).
3. If excerpts are empty, off-topic, or only partly relevant:
   - If the question is gibberish, unclear, or too vague, ask what crop or issue they mean
     in 1–3 sentences. Do NOT fill the answer with unrelated IPM or planting guides.
   - Otherwise combine useful excerpt text with focused agricultural guidance on what they
     actually asked — stay on topic; do not repeat generic filler.
4. Only refuse or stay very short when the user needs a specific product label,
   legal registration detail, or exact chemical rate you cannot support from the
   excerpts — then explain what is missing and suggest safe next steps (local
   extension, certified agronomist, official label).
5. Write for field use: brief overview, then clear numbered or bulleted actions.
   Name crops, pests, or diseases the user mentioned. Add a short "why it helps"
   when it improves clarity.
6. Match the language of the question. Be direct, constructive, and reasonably
   thorough — general guidance can be more expansive than a product lookup.
7. If the message includes photo notes, blend them briefly when relevant — do not output
   a separate "image analysis" block or repeat a vision checklist.
8. If the user asks who you are, greets you, or asks what you can do, answer in 3–5
   sentences about TerraMind and this agriculture guidance role only — do not dump
   unrelated retrieved topics or long IPM guides.
9. Do NOT start every answer with "Hello! I'm TerraMind..." — skip that opener unless
   the user greeted you or asked who you are.
10. Do not repeat or echo the user's question as a heading. Match the question language
   (Arabic, English, etc.).
11. Use clear Markdown: paragraphs, **bold** for key terms, ### headings for sections,
   and bullet or numbered lists for steps.

Safety:
- Do not invent brand names, product IDs, or precise application rates (L/ha, g/ai,
  tank mixes) without support in the excerpts.
- Prefer IPM before chemicals; if chemicals are discussed in general terms, remind
  users to follow local labels and regulations.
- For uncertain diagnoses, list likely causes and how to confirm (symptoms to scout,
  lab/extension options).
"""
)
