import json
import re

from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
from langchain_openai import ChatOpenAI

from core.rag.product.config import CHAT_MODEL


# Load embedding model once
model = SentenceTransformer(
    "all-MiniLM-L6-v2"
)


REFUSAL_PHRASES = (
    "i could not find relevant",
    "not available in the catalog",
    "i don't have enough information",
    "i do not have enough information",
    "cannot find relevant information",
    "no information available",
)


def is_refusal(text: str) -> bool:
    """
    Heuristic check for whether the system
    declined to answer instead of giving
    a substantive response.
    """

    lowered = text.lower()

    return any(
        phrase in lowered
        for phrase in REFUSAL_PHRASES
    )


def clean_answer(text: str) -> str:
    """
    Remove source references from
    generated answers.
    """

    if "### Sources" in text:
        text = text.split(
            "### Sources"
        )[0]

    return text.strip()


def similarity_score(
    golden: str,
    generated: str,
) -> float:
    """
    Semantic similarity using
    sentence embeddings.
    """

    emb1 = model.encode(
        golden
    )

    emb2 = model.encode(
        generated
    )

    score = cosine_similarity(
        [emb1],
        [emb2],
    )[0][0]

    return float(score)


def extract_facts(text: str) -> dict:
    """
    Extract agriculturally important facts.
    """

    text = text.lower()

    facts = {}

    # Percentages
    facts["percentages"] = re.findall(
        r"\d+(?:\.\d+)?%",
        text,
    )

    # g dosage
    facts["grams"] = re.findall(
        r"\d+(?:\.\d+)?\s*g\b",
        text,
    )

    # ml dosage
    facts["milliliters"] = re.findall(
        r"\d+(?:\.\d+)?\s*ml\b",
        text,
    )

    # g/L concentrations
    facts["g_per_l"] = re.findall(
        r"\d+(?:\.\d+)?\s*g\/l",
        text,
    )

    # jin water ratios
    facts["jin"] = re.findall(
        r"\d+(?:\.\d+)?\s*jin",
        text,
    )

    # days
    facts["days"] = re.findall(
        r"\d+\s*days?",
        text,
    )

    # applications per season
    facts["applications"] = re.findall(
        r"\d+\s*application[s]?\s*per\s*season",
        text,
    )

    return facts


# ---------------------------------------------------------------------
# Metric 2: Factual Correctness (RAGAS-style)
# ---------------------------------------------------------------------

# Lazily-created LLM used for claim
# decomposition and verification.
_eval_llm = None


def _get_eval_llm() -> ChatOpenAI:
    """
    Create (once) the LLM used for
    claim decomposition and verification.
    """

    global _eval_llm

    if _eval_llm is None:

        _eval_llm = ChatOpenAI(
            model=CHAT_MODEL,
            temperature=0,
        )

    return _eval_llm


def _parse_json_array(content: str) -> list:
    """
    Parse a JSON array from an LLM response,
    tolerating markdown code fences and
    surrounding text.
    """

    content = content.strip()

    if content.startswith("```"):

        content = content.strip("`")

        content = content.split(
            "\n",
            1,
        )[-1]

    match = re.search(
        r"\[.*\]",
        content,
        re.DOTALL,
    )

    if match:
        content = match.group(0)

    try:
        return json.loads(content)

    except json.JSONDecodeError:
        return []


CLAIM_DECOMPOSITION_PROMPT = (
    "Break the following answer into a list of short, self-contained, "
    "atomic factual claims. Each claim should state exactly one fact "
    "(e.g. one dosage, one safety interval, one product name, one "
    "application count). Ignore greetings, filler, and source citations.\n"
    "Return ONLY a JSON array of strings, with no other text.\n\n"
    "Answer:\n{text}"
)


def decompose_claims(text: str) -> list:
    """
    Break an answer into atomic
    factual claims using an LLM.
    """

    text = (text or "").strip()

    if not text:
        return []

    llm = _get_eval_llm()

    response = llm.invoke(
        CLAIM_DECOMPOSITION_PROMPT.format(
            text=text
        )
    )

    claims = _parse_json_array(
        response.content
    )

    return [
        str(claim).strip()
        for claim in claims
        if str(claim).strip()
    ]


CLAIM_VERIFICATION_PROMPT = (
    "Reference text:\n{reference}\n\n"
    "For each numbered claim below, decide whether the reference text "
    "supports it (confirms it or directly implies it).\n"
    "Return ONLY a JSON array of true/false values, in the same order "
    "as the claims, with no other text.\n\n"
    "Claims:\n{claims}"
)


def verify_claims(claims: list, reference: str) -> int:
    """
    Count how many claims are
    supported by the reference text.
    """

    reference = (reference or "").strip()

    if not claims or not reference:
        return 0

    llm = _get_eval_llm()

    numbered_claims = "\n".join(
        f"{i + 1}. {claim}"
        for i, claim in enumerate(claims)
    )

    response = llm.invoke(
        CLAIM_VERIFICATION_PROMPT.format(
            reference=reference,
            claims=numbered_claims,
        )
    )

    verdicts = _parse_json_array(
        response.content
    )

    return sum(
        1
        for verdict in verdicts
        if verdict is True
    )


def factual_correctness_score(
    golden: str,
    generated: str,
) -> float:
    """
    RAGAS-style Factual Correctness.

    Decomposes the golden and generated answers into
    atomic claims, then computes precision (claims in
    the generated answer supported by the golden answer),
    recall (golden claims supported by the generated
    answer), and their F1 as a 0-1 score.
    """

    golden_claims = decompose_claims(
        golden
    )

    generated_claims = decompose_claims(
        generated
    )

    if not golden_claims and not generated_claims:
        return 1.0

    if not golden_claims or not generated_claims:
        return 0.0

    precision = (
        verify_claims(generated_claims, golden)
        / len(generated_claims)
    )

    recall = (
        verify_claims(golden_claims, generated)
        / len(golden_claims)
    )

    if precision + recall == 0:
        return 0.0

    return (
        2 * precision * recall
        / (precision + recall)
    )


def agri_score(
    golden: str,
    generated: str,
) -> float:
    """
    Compare extracted agricultural facts.

    Returns a score between 0 and 1.
    """

    golden_facts = extract_facts(
        golden
    )

    generated_facts = extract_facts(
        generated
    )

    total = 0
    matched = 0

    for key in golden_facts:

        golden_values = set(
            golden_facts[key]
        )

        if not golden_values:
            continue

        generated_values = set(
            generated_facts.get(
                key,
                [],
            )
        )

        total += len(
            golden_values
        )

        matched += len(
            golden_values.intersection(
                generated_values
            )
        )

    if total == 0:
        return 1.0

    return matched / total