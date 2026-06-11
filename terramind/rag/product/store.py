"""Product RAG — build, load, and reset the Chroma vector index."""

# Product Vector Store
# 
# Responsible for converting Product RAG chunks into embeddings and
# storing them inside a dedicated Chroma vector database.
#
# Pipeline:
# Product Documents
# → Chunks
# → OpenAI Embeddings
# → Chroma Vector Store
#
# The Product RAG index is kept separate from the General RAG index
# to avoid cross-domain retrieval contamination.

from pathlib import Path
import shutil

from langchain_core.documents import Document
from langchain_openai import OpenAIEmbeddings
from langchain_chroma import Chroma

from terramind.rag.product.config import (
    CHROMA_PATH,
    EMBEDDING_MODEL,
)


# Check whether a Product RAG Chroma index already exists.
# Used to determine whether to load an existing index or build a new one.
def chroma_exists() -> bool:
    """
    Check whether a Chroma index already exists.
    """

    return (
        CHROMA_PATH / "chroma.sqlite3"
    ).exists()

# Create the embedding model used to transform text chunks
# into vector representations for semantic search.
def create_embedding_model() -> OpenAIEmbeddings:
    """
    Create the embedding model used
    by Product RAG.
    """

    return OpenAIEmbeddings(
        model=EMBEDDING_MODEL
    )

# Load an existing Product RAG vector store.
# This is used during retrieval to avoid rebuilding embeddings.
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

# Vector Store Builder
# 
# Create or load the Product RAG Chroma index.
#
# Behavior:
# - Load an existing index if available
# - Optionally rebuild from scratch when reset=True
# - Generate embeddings for all chunks
# - Persist vectors to disk for future retrieval
def build_vector_store(
    chunks: list[Document],
    reset: bool = False,
) -> Chroma:
    """
    Build a Chroma vector store from chunks.
    """
    
    # Initialize embedding model
    embeddings = (
        create_embedding_model()
    )
    
    # Ensure vector store directory exists
    CHROMA_PATH.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    # Rebuild mode:
    # remove the existing index before creating a new one
    if reset and chroma_exists():

        shutil.rmtree(
            CHROMA_PATH
        )

        print(
            f"Removed existing index: "
            f"{CHROMA_PATH}"
        )
    
    # Reuse an existing vector store if available
    if chroma_exists():

        db = load_vector_store()

        print(
            f"Loaded existing index "
            f"({db._collection.count()} vectors)"
        )

        return db


    # Generate embeddings and create a new Chroma index
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

# Development Test
# 
# End-to-end validation of the Product RAG indexing pipeline.
#
# Flow:
# Catalog
# → Products
# → Chunks
# → Embeddings
# → Chroma Vector Store
if __name__ == "__main__":
    
    # Load product catalog
    products = load_products(
        CATALOG_PATH
    )
    
    # Generate retrieval-ready chunks
    chunks = build_all_chunks(
        products
    )

    print(
        f"Products: {len(products)}"
    )

    print(
        f"Chunks: {len(chunks)}"
    )
    
    # Build Product RAG vector database
    db = build_vector_store(
        chunks,
        reset=True,
    )

    print(
        f"Vectors stored: "
        f"{db._collection.count()}"
    )