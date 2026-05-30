"""Split documents into retrieval-sized chunks."""

import json
from dataclasses import asdict, dataclass

from src.config import CHUNK_OVERLAP, CHUNK_SIZE
from src.document_loader import Document


@dataclass
class Chunk:
    id: str
    text: str
    document_id: str
    source: str
    title: str
    category: str
    chunk_index: int


def chunk_text(text: str, chunk_size: int = CHUNK_SIZE, overlap: int = CHUNK_OVERLAP) -> list[str]:
    """Split text into overlapping character chunks."""
    if len(text) <= chunk_size:
        return [text]

    chunks: list[str] = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        chunks.append(text[start:end].strip())
        if end >= len(text):
            break
        start = end - overlap
    return [c for c in chunks if c]


def chunk_documents(documents: list[Document]) -> list[Chunk]:
    """Turn each document into one or more chunks with metadata."""
    all_chunks: list[Chunk] = []

    for doc in documents:
        pieces = chunk_text(doc.text)
        for i, piece in enumerate(pieces):
            all_chunks.append(
                Chunk(
                    id=f"{doc.id}__chunk_{i}",
                    text=piece,
                    document_id=doc.id,
                    source=doc.source,
                    title=doc.title,
                    category=doc.category,
                    chunk_index=i,
                )
            )

    return all_chunks


def save_chunks_jsonl(chunks: list[Chunk], output_path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as f:
        for chunk in chunks:
            f.write(json.dumps(asdict(chunk), ensure_ascii=False) + "\n")


def load_chunks_jsonl(path) -> list[Chunk]:
    chunks: list[Chunk] = []
    with path.open(encoding="utf-8") as f:
        for line in f:
            row = json.loads(line)
            chunks.append(Chunk(**row))
    return chunks
