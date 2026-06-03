"""General RAG — public API used by terramind.models.general_rag."""

from langchain_chroma import Chroma
from langchain_core.documents import Document

from terramind.rag.general.chunk import chunk_document
from terramind.rag.general.config import DATA_PATH, RETRIEVAL_K
from terramind.rag.general.generate import generate_answer
from terramind.rag.general.load import load_document
from terramind.rag.general.retrieve import format_context, retrieve_chunks
from terramind.rag.general.store import build_chroma_db

_db: Chroma | None = None


def init_general_rag(reset: bool = False) -> Chroma:
    """Load or build the agriculture document Chroma index."""
    global _db
    doc = load_document(DATA_PATH)
    chunks = chunk_document(doc)
    _db = build_chroma_db(chunks, reset=reset)
    return _db


def get_general_db() -> Chroma:
    global _db
    if _db is None:
        _db = init_general_rag(reset=False)
    return _db


def answer_with_rag(db: Chroma, question: str, k: int = RETRIEVAL_K) -> dict:
    retrieved = retrieve_chunks(db, question, k=k)
    context = format_context(retrieved)
    answer = generate_answer(context, question)
    return {
        "answer": answer,
        "retrieved": retrieved,
        "context": context,
    }


def sources_from_retrieved(retrieved: list[Document]) -> list[dict]:
    seen: set[str] = set()
    sources: list[dict] = []
    for doc in retrieved:
        title = doc.metadata.get("title") or doc.metadata.get(
            "filename", "Document"
        )
        source = doc.metadata.get("source", "agriculture_knowledge")
        if source in seen:
            continue
        seen.add(source)
        sources.append({"title": title, "source": source, "section": None})
    return sources
