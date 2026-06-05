"""
Product RAG — build, load, and reset the Chroma vector index.

TODO: Move from Rag_Pc.py:
  - _chroma_exists(), build_chroma_db(docs, reset=False)
  - OpenAIEmbeddings + Chroma persist to vectorstore/chroma_products
  - Export: build_chroma_db(), get_or_create_db() helpers
See docs/PROJECT_STATUS.md (product migration).
"""


from pathlib import Path
import shutil

from langchain_core.documents import Document
from langchain_openai import OpenAIEmbeddings
from langchain_chroma import Chroma

from terramind.rag.product.config import (
    CHROMA_PATH,
    EMBEDDING_MODEL,
)


def chroma_exists() -> bool:
    """
    Check whether a Chroma index already exists.
    """

    return (
        CHROMA_PATH / "chroma.sqlite3"
    ).exists()


def create_embedding_model() -> OpenAIEmbeddings:
    """
    Create the embedding model used
    by Product RAG.
    """

    return OpenAIEmbeddings(
        model=EMBEDDING_MODEL
    )


def load_vector_store() -> Chroma:
    """
    Load an existing Chroma vector store.
    """

    embeddings = (
        create_embedding_model()
    )

    return Chroma(
        persist_directory=str(CHROMA_PATH),
        embedding_function=embeddings,
    )


def build_vector_store(
    chunks: list[Document],
    reset: bool = False,
) -> Chroma:
    """
    Build a Chroma vector store from chunks.
    """

    embeddings = (
        create_embedding_model()
    )

    CHROMA_PATH.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    if reset and chroma_exists():

        shutil.rmtree(
            CHROMA_PATH
        )

        print(
            f"Removed existing index: "
            f"{CHROMA_PATH}"
        )

    if chroma_exists():

        db = load_vector_store()

        print(
            f"Loaded existing index "
            f"({db._collection.count()} vectors)"
        )

        return db

    db = Chroma.from_documents(
        documents=chunks,
        embedding=embeddings,
        persist_directory=str(
            CHROMA_PATH
        ),
    )

    print(
        f"Built new index with "
        f"{len(chunks)} chunks"
    )

    return db



from terramind.rag.product.load import (
    load_products,
)

from terramind.rag.product.chunk import (
    build_all_chunks,
)

from terramind.rag.product.config import (
    CATALOG_PATH,
)


if __name__ == "__main__":

    products = load_products(
        CATALOG_PATH
    )

    chunks = build_all_chunks(
        products
    )

    print(
        f"Products: {len(products)}"
    )

    print(
        f"Chunks: {len(chunks)}"
    )

    db = build_vector_store(
        chunks,
        reset=True,
    )

    print(
        f"Vectors stored: "
        f"{db._collection.count()}"
    )