"""
LLM-as-a-judge metrics for the generation stage.

A single gpt-4o-mini call per question scores the answer against the
question, the retrieved context, and the golden reference — bundled
into one structured call to keep judge cost to one extra LLM call
per evaluated question.
"""

from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field

from core.rag.product.config import CHAT_MODEL


class JudgeScores(BaseModel):
    faithfulness: float = Field(
        description=(
            "0-1. Are all claims in the answer strictly supported "
            "by the retrieved context, with no invented details?"
        )
    )
    answer_relevancy: float = Field(
        description="0-1. Does the answer address what the user actually asked?"
    )
    completeness_question: float = Field(
        description="0-1. Does the answer fully and comprehensively answer the question?"
    )
    completeness_context: float = Field(
        description=(
            "0-1. Does the answer make full use of the relevant information "
            "available in the retrieved context?"
        )
    )
    context_precision: float = Field(
        description="0-1. Is the retrieved context relevant to the question (low noise)?"
    )
    context_recall: float = Field(
        description=(
            "0-1. Does the retrieved context contain all the evidence needed "
            "to produce the golden answer?"
        )
    )
    correctness: float = Field(
        description="0-1. Is the answer factually correct relative to the golden answer?"
    )
    coherence_tone: float = Field(
        description=(
            "0-1. Is the answer clear, well-organized, concise, and appropriately toned?"
        )
    )


JUDGE_PROMPT = """You are a strict evaluator for a Retrieval-Augmented Generation (RAG) assistant.
Score the generated answer on each criterion below, from 0.0 (fails) to 1.0 (excellent).
Do not default to high scores: reserve 1.0 for answers with no flaws whatsoever, and penalize
any verbosity, missing details, unsupported claims, or stylistic mismatch with the golden answer.

Question:
{question}

Retrieved context (what the assistant had available):
{context}

Golden / reference answer:
{golden}

Generated answer:
{generated}

Score: faithfulness, answer_relevancy, completeness_question, completeness_context,
context_precision, context_recall, correctness, coherence_tone.
"""


_judge_llm = None


def get_judge_llm():
    global _judge_llm

    if _judge_llm is None:
        _judge_llm = ChatOpenAI(
            model=CHAT_MODEL,
            temperature=0,
        ).with_structured_output(JudgeScores)

    return _judge_llm


def judge_answer(
    question: str,
    context: str,
    golden: str,
    generated: str,
) -> dict:
    """
    Run the bundled LLM-judge call and
    return scores as a plain dict.
    """

    llm = get_judge_llm()

    prompt = JUDGE_PROMPT.format(
        question=question,
        context=context or "(no context retrieved)",
        golden=golden,
        generated=generated,
    )

    result: JudgeScores = llm.invoke(prompt)

    return result.model_dump()
