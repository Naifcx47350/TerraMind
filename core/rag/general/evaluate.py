"""General RAG — optional chunk similarity metrics (CLI / dev only)."""

from langchain_classic.evaluation import EvaluatorType, load_evaluator
from langchain_core.documents import Document
from langchain_openai import OpenAIEmbeddings

from core.rag.general.config import EMBEDDING_MODEL


def evaluate_chunk_similarity(
    chunk_docs: list[Document], max_pairs: int = 5
) -> list[dict]:
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
