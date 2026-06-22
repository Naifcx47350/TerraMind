import re
from core.rag.product.load import load_products
from core.rag.product.config import CATALOG_PATH

_PRODUCTS = None

def get_product_names():

    global _PRODUCTS

    if _PRODUCTS is None:

        products = load_products(
            CATALOG_PATH
        )

        _PRODUCTS = [
            p.metadata["product_name"]
            for p in products
        ]

    return _PRODUCTS


def detect_product_name(
    question: str,
) -> str | None:

    q = question.lower()

    for name in get_product_names():

        if name.lower() in q:
            return name

    return None

def detect_product_id(
    question: str,
) -> str | None:

    match = re.search(
        r"\b(AF|PN)\d{4}\b",
        question,
        re.IGNORECASE,
    )

    if match:
        return match.group().upper()

    return None


if __name__ == "__main__":

    print(
        detect_product_id(
            "How should I apply AF0009?"
        )
    )

    print(
        detect_product_id(
            "Tell me about PN0002"
        )
    )
    
    print(
        detect_product_name(
            "How should I apply Citrus Bacteria Clear?"
        )
    )