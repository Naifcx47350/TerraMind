# =============================================================================
# TerraMind — learning RAG script (load → chunk → store → retrieve → generate)
# =============================================================================

from pathlib import Path
import shutil

from dotenv import load_dotenv
from langchain_chroma import Chroma
from langchain_classic.evaluation import EvaluatorType, load_evaluator
from langchain_core.documents import Document
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter

load_dotenv()

# -----------------------------------------------------------------------------
# Config — paths and model names
# -----------------------------------------------------------------------------
PROJECT_ROOT = Path(__file__).resolve().parent
DATA_PATH = PROJECT_ROOT / "data/raw/text/Pest_Management_FAO.md"
CHROMA_PATH = PROJECT_ROOT / "vectorstore" / "chroma"

EMBEDDING_MODEL = "text-embedding-3-small"  # do not rely on ada-002 default
CHAT_MODEL = "gpt-3.5-turbo"
RETRIEVAL_K = 4

RAG_PROMPT = ChatPromptTemplate.from_template(
    """You are an agriculture support assistant. Answer using ONLY the context below.
If the context does not contain enough information, say so clearly.

Context:
{document}

Question:
{question}

Rules:
- Be concise and practical.
- Do not invent product names or dosages.
- Match the language of the question.
"""
)


# -----------------------------------------------------------------------------
# 1. Load document — read file and attach metadata for sources
# -----------------------------------------------------------------------------
def _guess_title(text: str, filename: str) -> str:
    for line in text.splitlines():
        line = line.strip()
        if line.startswith("# "):
            return line.lstrip("# ").strip()
    return Path(filename).stem.replace("_", " ")


def load_document(file_path: str | Path) -> Document:
    path = Path(file_path)
    text = path.read_text(encoding="utf-8")
    return Document(
        page_content=text,
        metadata={
            "source": str(path),
            "filename": path.name,
            "title": _guess_title(text, path.name),
            "file_type": path.suffix.lstrip("."),
        },
    )


# -----------------------------------------------------------------------------
# 2. Chunking — split long text into retrieval-sized pieces
# -----------------------------------------------------------------------------
def chunk_document(doc: Document) -> list[Document]:
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=500,
        length_function=len,
        add_start_index=True,
    )
    return splitter.split_documents([doc])


# -----------------------------------------------------------------------------
# 3. Vector store — embed chunks and persist in Chroma (reuse if already built)
# -----------------------------------------------------------------------------
def _chroma_exists() -> bool:
    return (CHROMA_PATH / "chroma.sqlite3").exists()


def build_chroma_db(chunk_docs: list[Document], reset: bool = False) -> Chroma:
    CHROMA_PATH.parent.mkdir(parents=True, exist_ok=True)
    embeddings = OpenAIEmbeddings(model=EMBEDDING_MODEL)

    if reset and _chroma_exists():
        shutil.rmtree(CHROMA_PATH)
        print(f"Removed existing index at {CHROMA_PATH}")

    if _chroma_exists():
        db = Chroma(
            persist_directory=str(CHROMA_PATH),
            embedding_function=embeddings,
        )
        print(
            f"Loaded existing Chroma index ({db._collection.count()} vectors)")
        return db

    db = Chroma.from_documents(
        chunk_docs,
        embedding=embeddings,
        persist_directory=str(CHROMA_PATH),
    )
    print(f"Built new index with {len(chunk_docs)} chunks")
    return db


# -----------------------------------------------------------------------------
# 4. Retrieval — find chunks most similar to the user question
# -----------------------------------------------------------------------------
def retrieve_chunks(db: Chroma, question: str, k: int = RETRIEVAL_K) -> list[Document]:
    return db.similarity_search(question, k=k)


def format_context(retrieved: list[Document]) -> str:
    return "\n\n---\n\n".join(doc.page_content for doc in retrieved)


# -----------------------------------------------------------------------------
# 5. Generation — send context + question to the LLM via prompt template
# -----------------------------------------------------------------------------
def answer_with_rag(db: Chroma, question: str, k: int = RETRIEVAL_K) -> dict:
    retrieved = retrieve_chunks(db, question, k=k)
    context = format_context(retrieved)

    messages = RAG_PROMPT.invoke({"document": context, "question": question})
    llm = ChatOpenAI(model=CHAT_MODEL, temperature=0.2)
    response = llm.invoke(messages)

    return {
        "answer": response.content,
        "retrieved": retrieved,
        "context": context,
    }


# -----------------------------------------------------------------------------
# 6. Optional metric — embedding distance between adjacent chunks
# -----------------------------------------------------------------------------
def evaluate_chunk_similarity(chunk_docs: list[Document], max_pairs: int = 5) -> list[dict]:
    embeddings = OpenAIEmbeddings(model=EMBEDDING_MODEL)
    evaluator = load_evaluator(
        EvaluatorType.PAIRWISE_EMBEDDING_DISTANCE,
        embeddings=embeddings,
    )

    results: list[dict] = []
    for i in range(min(max_pairs, max(0, len(chunk_docs) - 1))):
        score = evaluator.evaluate_string_pairs(
            prediction=chunk_docs[i].page_content,
            prediction_b=chunk_docs[i + 1].page_content,
        )
        results.append(
            {
                "pair": (i, i + 1),
                "score": score.get("score"),
                "metric": evaluator.evaluation_name,
            }
        )
    return results


# -----------------------------------------------------------------------------
# Main — run the pipeline
# -----------------------------------------------------------------------------
if __name__ == "__main__":
    query = (
        "A potato farmer has repeated late blight outbreaks and wants to reduce pesticide use. "
        "Based on the provided document, what integrated disease management steps should they take "
        "before relying on fungicides, and when should fungicide application be planned?"
    )

    doc = load_document(DATA_PATH)
    chunks = chunk_document(doc)
    print(f"Split 1 document into {len(chunks)} chunks")

    db = build_chroma_db(chunks)

    print("\n--- Retrieved chunks ---")
    retrieved = retrieve_chunks(db, query)
    for i, hit in enumerate(retrieved, start=1):
        print(f"\nResult {i} | {hit.metadata.get('title', 'n/a')}")
        print(hit.page_content[:300], "...")

    print("\n--- RAG answer ---")
    result = answer_with_rag(db, query)
    sources = [doc.metadata.get('source', 'n/a') for doc in retrieved]

    formatted_response = f"""
    {result["answer"]}
    \n\n---\n\n
    Sources: {sources}
    """
    print(formatted_response)

    # Uncomment to run the optional chunk-similarity check (extra API calls):
    # similarity = evaluate_chunk_similarity(chunks, max_pairs=5)
    # for row in similarity:
    #     print(f"  chunks {row['pair']}: score={row['score']:.4f}")
