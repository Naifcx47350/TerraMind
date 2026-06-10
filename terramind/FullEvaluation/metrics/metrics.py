import re

from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity


# Load embedding model once
model = SentenceTransformer(
    "all-MiniLM-L6-v2"
)


def normalize(text: str) -> str:
    """
    Lowercase and remove punctuation
    for exact matching.
    """

    text = text.lower()

    text = re.sub(
        r"[^\w\s]",
        "",
        text,
    )

    return text.strip()


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