"""Embed chunks and build the Chroma vector store."""

import _bootstrap  # noqa: F401

from dotenv import load_dotenv

from src.chunking import load_chunks_jsonl
from src.config import CHUNKS_PATH
from src.vector_store import add_chunks, reset_collection

load_dotenv()


def main():
    chunks = load_chunks_jsonl(CHUNKS_PATH)
    if not chunks:
        raise SystemExit(
            f"No chunks found at {CHUNKS_PATH}. Run 01_ingest_documents.py and 02_create_chunks.py first."
        )

    reset_collection()
    count = add_chunks(chunks)
    print(f"Stored {count} chunks in Chroma vector store.")


if __name__ == "__main__":
    main()
