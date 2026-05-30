"""Chunk processed documents and save chunks.jsonl."""

import _bootstrap  # noqa: F401

from dotenv import load_dotenv

from src.chunking import chunk_documents, save_chunks_jsonl
from src.config import CHUNKS_PATH, DOCUMENTS_PATH
from src.document_loader import load_documents_jsonl

load_dotenv()


def main():
    documents = load_documents_jsonl(DOCUMENTS_PATH)
    chunks = chunk_documents(documents)
    save_chunks_jsonl(chunks, CHUNKS_PATH)
    print(f"Created {len(chunks)} chunks from {len(documents)} documents -> {CHUNKS_PATH}")


if __name__ == "__main__":
    main()
