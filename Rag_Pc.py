# =============================================================================
# TerraMind — Product Catalog RAG (Excel → row documents → store → retrieve → answer)
# =============================================================================

import argparse
import threading
from pathlib import Path
import shutil

import pandas as pd
from dotenv import load_dotenv
from langchain_chroma import Chroma
from langchain_core.documents import Document
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter

load_dotenv()

# -----------------------------------------------------------------------------
# Config — paths, model names, Excel layout
# -----------------------------------------------------------------------------
PROJECT_ROOT = Path(__file__).resolve().parent
CATALOG_PATH = PROJECT_ROOT / "data/raw/text/ProductCatalog(En).xlsx"
CATEGORY_PATH = PROJECT_ROOT / "data/raw/text/Product_catagorys(En).xlsx"

# Separate store so product vectors don't mix with general RAG (vectorstore/chroma/)
CHROMA_PATH = PROJECT_ROOT / "vectorstore" / "chroma_products"

EMBEDDING_MODEL = "text-embedding-3-small"
CHAT_MODEL = "gpt-4o-mini"
RETRIEVAL_K = 4

# Excel columns
COL_PRODUCT_ID = "Product ID"
# original Chinese-derived label; not used in RAG text
COL_LEGACY_NAME = "Product Name"
COL_PRODUCT_NAME = "English name"  # canonical English product name for users

# Fields turned into readable product text (display label -> Excel column).
# We omit COL_LEGACY_NAME — it duplicates COL_PRODUCT_NAME in practice.
PRODUCT_FIELDS = {
    "Product Name": COL_PRODUCT_NAME,
    "Product Type": "Product Type",
    "Corresponding Crops/Plants": "Corresponding crops/plants",
    "Main Ingredients": "Main ingredients",
    "Usage and Dosage": "Usage and dosage",
    "Instructions for Use (dilute with water)": "Instructions for use (dilute with water)",
    "Specification": "Specification",
    "User Manual": "User Manual",
}

RAG_PROMPT = ChatPromptTemplate.from_template(
    """You are TerraMind product catalog assistant — helping growers choose and use
products safely from the company catalog.

Retrieved product records:
{context}

User message (may include brief notes from an uploaded crop photo):
{question}

How to respond:
- Answer what they actually asked first (e.g. what is wrong with the crop, is it serious,
  which catalog product fits, how to mix/apply, timing, safety) — not a generic template.
- If they sent a photo: weave a short observation into your answer (symptoms, severity);
  do not output a separate "image analysis" report or repeat a numbered vision checklist.
- When a product recommendation is needed: name the best match from the catalog and explain
  why it fits the crop/problem; give use, dilution, dosage, and crops only where the
  catalog text provides them.
- Do not force every reply to list Product ID, User Manual, and all catalog fields.
  Include IDs or manual quotes only when they help the user.
- If several products match, lead with the strongest fit; mention one alternative only if useful.
- If a detail is missing in the catalog, say so once and point to the product label — never
  invent rates, ingredients, or SKUs.

Formatting:
- Use clear Markdown the chat can render: short paragraphs, **bold** for emphasis,
  ### headings for sections, and bullet or numbered lists for steps.

Rules:
- Product facts, rates, and SKUs must come ONLY from the retrieved records above.
- Be practical and concise unless they ask for full label-level detail.
"""
)


# -----------------------------------------------------------------------------
# 1. Load catalog — read Excel rows into product DataFrame (+ optional category)
# -----------------------------------------------------------------------------
def _clean(value) -> str:
    """Turn a cell into a trimmed string; NaN/None -> empty string."""
    if pd.isna(value):
        return ""
    return str(value).strip()


def _display_product_name(row: pd.Series) -> str:
    """Canonical name for RAG: English name, else legacy Product Name column."""
    name = _clean(row.get(COL_PRODUCT_NAME))
    if name:
        return name
    return _clean(row.get(COL_LEGACY_NAME))


def load_catalog() -> pd.DataFrame:
    """Load the product catalog and best-effort attach category columns."""
    catalog = pd.read_excel(CATALOG_PATH)

    if CATEGORY_PATH.exists():
        categories = pd.read_excel(CATEGORY_PATH)
        # Category file uses English-style names; join on English name, not legacy column
        catalog = catalog.merge(
            categories,
            how="left",
            left_on=COL_PRODUCT_NAME,
            right_on="Product Name",
        )

    return catalog


# -----------------------------------------------------------------------------
# 2. Build documents — one Document per product row, with metadata for sources
# -----------------------------------------------------------------------------
def _row_to_text(row: pd.Series) -> str:
    parts = []
    for label, column in PRODUCT_FIELDS.items():
        if label == "Product Name":
            value = _display_product_name(row)
        else:
            value = _clean(row.get(column))
        if value:
            parts.append(f"{label}: {value}")
    return "\n".join(parts)


def build_product_documents(catalog: pd.DataFrame) -> list[Document]:
    documents: list[Document] = []

    for _, row in catalog.iterrows():
        text = _row_to_text(row)
        if not text:
            continue

        metadata = {
            "product_id": _clean(row.get(COL_PRODUCT_ID)),
            "product_name": _display_product_name(row),
            "product_type": _clean(row.get("Product Type")),
            "crops": _clean(row.get("Corresponding crops/plants")),
            "primary_category": _clean(row.get("Primary Category")),
            "secondary_category": _clean(row.get("Secondary Category")),
            "source": CATALOG_PATH.name,
        }
        documents.append(Document(page_content=text, metadata=metadata))

    return documents


# -----------------------------------------------------------------------------
# 3. Chunking — most product entries fit in one chunk; split only long ones
# -----------------------------------------------------------------------------
def chunk_documents(documents: list[Document]) -> list[Document]:
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=1500,
        chunk_overlap=200,
        length_function=len,
        add_start_index=True,
    )
    return splitter.split_documents(documents)


# -----------------------------------------------------------------------------
# 4. Vector store — embed and persist in Chroma (reuse if already built)
# -----------------------------------------------------------------------------
def _chroma_exists() -> bool:
    return (CHROMA_PATH / "chroma.sqlite3").exists()


def build_chroma_db(chunk_docs: list[Document], reset: bool = False) -> Chroma:
    CHROMA_PATH.parent.mkdir(parents=True, exist_ok=True)
    embeddings = OpenAIEmbeddings(model=EMBEDDING_MODEL)

    if reset and _chroma_exists():
        shutil.rmtree(CHROMA_PATH)
        print(f"Removed existing index at {CHROMA_PATH}")

    if _chroma_exists():
        db = Chroma(
            persist_directory=str(CHROMA_PATH),
            embedding_function=embeddings,
        )
        print(
            f"Loaded existing product index ({db._collection.count()} vectors)")
        return db

    db = Chroma.from_documents(
        chunk_docs,
        embedding=embeddings,
        persist_directory=str(CHROMA_PATH),
    )
    print(f"Built new product index with {len(chunk_docs)} chunks")
    return db


# -----------------------------------------------------------------------------
# 5. Retrieval — find products most similar to the question
# -----------------------------------------------------------------------------
def retrieve_products(db: Chroma, question: str, k: int = RETRIEVAL_K) -> list[Document]:
    from langchain_core.documents import Document

    from terramind.rag.scoring import distance_to_relevance

    pairs = db.similarity_search_with_score(question, k=k)
    out: list[Document] = []
    for doc, distance in pairs:
        meta = dict(doc.metadata)
        meta["relevance_score"] = distance_to_relevance(distance)
        out.append(Document(page_content=doc.page_content, metadata=meta))
    return out


def format_context(retrieved: list[Document]) -> str:
    blocks = []
    for i, doc in enumerate(retrieved, start=1):
        name = doc.metadata.get("product_name", "Unknown product")
        blocks.append(f"[Product {i}] {name}\n{doc.page_content}")
    return "\n\n---\n\n".join(blocks)


# -----------------------------------------------------------------------------
# 6. Generation — context + question to the LLM
# -----------------------------------------------------------------------------
def _format_messages_for_print(messages) -> str:
    """Turn LangChain messages into readable text for the terminal."""
    lines = []
    for msg in messages:
        role = getattr(msg, "type", None) or msg.__class__.__name__
        lines.append(f"[{role}]\n{msg.content}")
    return "\n\n".join(lines)


_db: Chroma | None = None
_init_lock = threading.Lock()


def init_product_rag(reset: bool = False) -> Chroma:
    """Load or build the product Chroma index (used by CLI and rag_api.py)."""
    global _db
    catalog = load_catalog()
    documents = build_product_documents(catalog)
    chunks = chunk_documents(documents)
    _db = build_chroma_db(chunks, reset=reset)
    return _db


def get_product_db() -> Chroma:
    """Return a cached DB handle; builds the index on first call if needed."""
    global _db
    if _db is not None:
        return _db
    with _init_lock:
        if _db is None:
            _db = init_product_rag(reset=False)
    return _db


def sources_from_retrieved(retrieved: list[Document]) -> list[dict]:
    """Format retrieval hits for FrontPage /api/ask (SourceDoc-compatible dicts)."""
    from terramind.rag.scoring import sources_from_retrieved as _sources_scored

    return _sources_scored("product", retrieved)


def answer_with_rag(db: Chroma, question: str, k: int = RETRIEVAL_K) -> dict:
    retrieved = retrieve_products(db, question, k=k)
    context = format_context(retrieved)

    prompt_value = RAG_PROMPT.invoke(
        {"context": context, "question": question})
    messages = prompt_value.to_messages()
    prompt_text = _format_messages_for_print(messages)

    llm = ChatOpenAI(model=CHAT_MODEL, temperature=0.2)
    response = llm.invoke(messages)

    return {
        "answer": response.content,
        "question": question,
        "prompt_text": prompt_text,
        "retrieved": retrieved,
        "context": context,
    }


def stream_answer_with_rag(db: Chroma, question: str, k: int = RETRIEVAL_K):
    """Retrieve catalog rows, then stream LLM tokens."""
    from terramind.rag.llm_stream import stream_chat_tokens

    retrieved = retrieve_products(db, question, k=k)
    context = format_context(retrieved)
    prompt_value = RAG_PROMPT.invoke({"context": context, "question": question})
    messages = prompt_value.to_messages()
    token_gen = stream_chat_tokens(messages, model=CHAT_MODEL, temperature=0.2)
    return retrieved, token_gen


# -----------------------------------------------------------------------------
# Main — run the pipeline
# -----------------------------------------------------------------------------
DEFAULT_QUESTION = (
    "what catgorys of usage dose the 10% Glufosinate-Ammonium belong too, and how can i use it?"
)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="TerraMind product catalog RAG")
    parser.add_argument(
        "--reset",
        action="store_true",
        help="Delete and rebuild the Chroma index (required after changing PRODUCT_FIELDS or name logic)",
    )
    parser.add_argument(
        "question",
        nargs="?",
        default=DEFAULT_QUESTION,
        help="Question about a specific product (default: Citrus Bacteria Clear instructions)",
    )
    args = parser.parse_args()

    db = init_product_rag(reset=args.reset)
    print(f"Product RAG ready ({db._collection.count()} vectors in index)")

    print("\n--- Retrieved products ---")
    for i, hit in enumerate(retrieve_products(db, args.question), start=1):
        print(f"\nProduct {i} | {hit.metadata.get('product_name', 'n/a')} "
              f"({hit.metadata.get('product_id', 'n/a')})")
        print(hit.page_content[:250], "...")

    print("\n" + "=" * 70)
    print("QUESTION")
    print("=" * 70)
    print(args.question)

    result = answer_with_rag(db, args.question)

    print("\n" + "=" * 70)
    print("PROMPT SENT TO LLM")
    print("=" * 70)
    print(result["prompt_text"])

    print("\n" + "=" * 70)
    print("RAG ANSWER")
    print("=" * 70)
    print(result["answer"])
