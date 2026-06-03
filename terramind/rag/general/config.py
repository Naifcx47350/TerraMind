"""General RAG — paths and model settings."""

from pathlib import Path

from dotenv import load_dotenv
from langchain_core.prompts import ChatPromptTemplate

load_dotenv()

REPO_ROOT = Path(__file__).resolve().parents[3]
DATA_PATH = REPO_ROOT / "data/raw/text/Pest_Management_FAO.md"
CHROMA_PATH = REPO_ROOT / "vectorstore" / "chroma"

EMBEDDING_MODEL = "text-embedding-3-small"
CHAT_MODEL = "gpt-4o-mini"
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
