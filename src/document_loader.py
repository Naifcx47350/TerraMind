"""Load text documents from a directory."""

import json
from dataclasses import asdict, dataclass
from pathlib import Path

from src.config import PROJECT_ROOT, SAMPLE_DOCS_DIR
from src.text_cleaner import clean_text


@dataclass
class Document:
    id: str
    text: str
    source: str
    title: str
    category: str = "general"


def _guess_title(text: str, filename: str) -> str:
    for line in text.split("\n"):
        if line.lower().startswith("title:"):
            return line.split(":", 1)[1].strip()
        if line.lower().startswith("product:"):
            return line.split(":", 1)[1].strip()
    return Path(filename).stem.replace("_", " ").title()


def _guess_category(text: str, filename: str) -> str:
    if filename.startswith("product_"):
        return "product"
    if "safety" in filename:
        return "safety"
    return "agriculture"


def load_documents_from_dir(directory: Path | None = None) -> list[Document]:
    """Load all .txt files from a directory into Document objects."""
    directory = directory or SAMPLE_DOCS_DIR
    documents: list[Document] = []

    for path in sorted(directory.glob("*.txt")):
        raw = path.read_text(encoding="utf-8")
        text = clean_text(raw)
        if not text:
            continue

        doc_id = path.stem
        documents.append(
            Document(
                id=doc_id,
                text=text,
                source=str(path.relative_to(PROJECT_ROOT)),
                title=_guess_title(text, path.name),
                category=_guess_category(text, path.name),
            )
        )

    return documents


def save_documents_jsonl(documents: list[Document], output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as f:
        for doc in documents:
            f.write(json.dumps(asdict(doc), ensure_ascii=False) + "\n")


def load_documents_jsonl(path: Path) -> list[Document]:
    documents: list[Document] = []
    with path.open(encoding="utf-8") as f:
        for line in f:
            row = json.loads(line)
            documents.append(Document(**row))
    return documents
