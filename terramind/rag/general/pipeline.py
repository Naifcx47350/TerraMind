"""General RAG — public API used by terramind.models.general_rag."""

from langchain_chroma import Chroma
from langchain_core.documents import Document

from terramind.rag.general.chunk import chunk_documents
from terramind.rag.general.config import RETRIEVAL_K
from terramind.rag.general.generate import generate_answer
from terramind.rag.general.load import load_documents
from terramind.rag.general.retrieve import format_context, retrieve_chunks
from terramind.rag.general.store import _chroma_exists, build_chroma_db
from terramind.rag.scoring import sources_from_retrieved as _sources_from_retrieved

_db: Chroma | None = None


def init_general_rag(reset: bool = False) -> Chroma:
    """Load corpus from data dir, chunk, and build or open the Chroma index."""
    global _db
    if reset or not _chroma_exists():
        print("Loading general RAG corpus...")
        docs = load_documents()
        chunks = chunk_documents(docs)
        print(f"Indexed {len(docs)} document(s) -> {len(chunks)} chunks")
        _db = build_chroma_db(chunks, reset=reset)
    else:
        _db = build_chroma_db([], reset=False)
    return _db


def get_general_db() -> Chroma:
    global _db
    if _db is None:
        _db = init_general_rag(reset=False)
    return _db


def answer_with_rag(
    db: Chroma,
    retrieval_query: str,
    *,
    generation_prompt: str | None = None,
    k: int = RETRIEVAL_K,
) -> dict:
    """
    Search with a short retrieval_query (current question + optional brief image text).
    Generate with generation_prompt (may include conversation history).
    """
    gen_prompt = generation_prompt or retrieval_query
    retrieved = retrieve_chunks(db, retrieval_query, k=k)
    context = format_context(retrieved)
    answer = generate_answer(context, gen_prompt)
    return {
        "answer": answer,
        "retrieved": retrieved,
        "context": context,
    }


def sources_from_retrieved(retrieved: list[Document]) -> list[dict]:
    return _sources_from_retrieved("general", retrieved)
