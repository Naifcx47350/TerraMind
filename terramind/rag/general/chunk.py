"""General RAG — markdown-aware splitting with size limits for large sections."""

from langchain_core.documents import Document
from langchain_text_splitters import (
    MarkdownHeaderTextSplitter,
    RecursiveCharacterTextSplitter,
)

from terramind.rag.general.config import (
    CHUNK_OVERLAP,
    CHUNK_SIZE,
    MARKDOWN_HEADERS,
)


def _merge_parent_metadata(chunk: Document, parent: Document) -> Document:
    merged = dict(parent.metadata)
    merged.update(chunk.metadata)
    chunk.metadata = merged
    return chunk


def chunk_document(doc: Document) -> list[Document]:
    """Split by markdown headings first, then by size for long sections."""
    md_splitter = MarkdownHeaderTextSplitter(
        headers_to_split_on=MARKDOWN_HEADERS,
        strip_headers=False,
    )
    try:
        section_docs = md_splitter.split_text(doc.page_content)
    except Exception:
        section_docs = [
            Document(page_content=doc.page_content, metadata=dict(doc.metadata))
        ]

    if not section_docs:
        section_docs = [
            Document(page_content=doc.page_content, metadata=dict(doc.metadata))
        ]

    for chunk in section_docs:
        _merge_parent_metadata(chunk, doc)

    size_splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
        length_function=len,
        add_start_index=True,
    )
    return size_splitter.split_documents(section_docs)


def chunk_documents(docs: list[Document]) -> list[Document]:
    chunks: list[Document] = []
    for doc in docs:
        chunks.extend(chunk_document(doc))
    return chunks
