"""General RAG — similarity search and context formatting."""

from langchain_chroma import Chroma
from langchain_core.documents import Document

from terramind.rag.general.config import RETRIEVAL_K


def retrieve_chunks(db: Chroma, question: str, k: int = RETRIEVAL_K) -> list[Document]:
    return db.similarity_search(question, k=k)


def format_context(retrieved: list[Document]) -> str:
    return "\n\n---\n\n".join(doc.page_content for doc in retrieved)
