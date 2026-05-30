"""Load sample documents and save them as processed JSONL."""

import _bootstrap  # noqa: F401

from dotenv import load_dotenv

from src.config import DOCUMENTS_PATH, SAMPLE_DOCS_DIR
from src.document_loader import load_documents_from_dir, save_documents_jsonl

load_dotenv()


def main():
    documents = load_documents_from_dir(SAMPLE_DOCS_DIR)
    save_documents_jsonl(documents, DOCUMENTS_PATH)
    print(f"Loaded {len(documents)} documents -> {DOCUMENTS_PATH}")
    for doc in documents:
        print(f"  - {doc.id}: {doc.title} ({doc.category})")


if __name__ == "__main__":
    main()
