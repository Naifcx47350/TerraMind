"""General RAG — load markdown/text documents."""

from pathlib import Path

from langchain_core.documents import Document


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
