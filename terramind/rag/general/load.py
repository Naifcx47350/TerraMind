"""General RAG — load and clean markdown/text documents."""

import re
from pathlib import Path

from langchain_core.documents import Document

from terramind.rag.general.config import (
    DATA_PATH,
    GENERAL_DATA_DIR,
    SUPPORTED_EXTENSIONS,
)
from terramind.rag.source_display import clean_heading_title

# Line-level patterns common across reports, manuals, and licenses (not crop-specific).
_BOILERPLATE_PATTERNS: tuple[re.Pattern[str], ...] = (
    re.compile(r"^ISBN[\s:]", re.I),
    re.compile(r"^©\s", re.I),
    re.compile(r"^All rights reserved", re.I),
    re.compile(r"creativecommons\.org", re.I),
    re.compile(r"^https?://doi\.org/", re.I),
    re.compile(r"^Under the terms of (this|the) licen", re.I),
    re.compile(r"^Third[- ]party materials", re.I),
    re.compile(r"^Required citation\s*:", re.I),
    re.compile(r"^The designations employed", re.I),
    re.compile(r"^The views expressed in this", re.I),
    re.compile(r"^Any dispute arising under this licen", re.I),
    re.compile(r"^Queries regarding rights and licen", re.I),
    re.compile(r"^Sales, rights and licensing", re.I),
    re.compile(r"^Some rights reserved\.", re.I),
)

_SKIP_SECTION_TITLES = frozenset(
    {
        "contents",
        "table of contents",
        "list of figures",
        "list of tables",
    }
)

_PAGE_NUMBER = re.compile(r"^[ivxlc\d]+\s*$", re.I)
_TABLE_SEP = re.compile(r"^\|[\s\-:|]+\|\s*$")


def _guess_title(text: str, filename: str) -> str:
    for line in text.splitlines():
        line = line.strip()
        if line.startswith("# "):
            return line.lstrip("# ").strip()
    return Path(filename).stem.replace("_", " ")


def _is_boilerplate_line(line: str) -> bool:
    s = line.strip()
    if not s:
        return False
    if len(s) <= 4 and _PAGE_NUMBER.match(s):
        return True
    if _TABLE_SEP.match(s):
        return True
    return any(p.search(s) for p in _BOILERPLATE_PATTERNS)


def _heading_level(line: str) -> tuple[int, str] | None:
    m = re.match(r"^(#{1,6})\s+(.+)$", line.strip())
    if not m:
        return None
    return len(m.group(1)), m.group(2).strip()


def strip_boilerplate(text: str) -> str:
    """Remove generic front-matter noise; keep technical body text for any corpus."""
    lines = text.splitlines()
    out: list[str] = []
    skip_section = False
    skip_section_level = 0

    for line in lines:
        heading = _heading_level(line)
        if heading:
            level, title = heading
            key = title.lower().rstrip(":")
            if key in _SKIP_SECTION_TITLES:
                skip_section = True
                skip_section_level = level
                continue
            if skip_section and level <= skip_section_level:
                skip_section = False

        if skip_section:
            continue
        if _is_boilerplate_line(line):
            continue
        out.append(line)

    # Drop consecutive duplicate lines (repeated titles in PDF→MD exports).
    deduped: list[str] = []
    prev: str | None = None
    for line in out:
        key = line.strip()
        if key and key == prev:
            continue
        deduped.append(line)
        prev = key if key else prev

    cleaned = "\n".join(deduped)
    cleaned = re.sub(r"\n{4,}", "\n\n\n", cleaned)
    return cleaned.strip()


def load_document(file_path: str | Path) -> Document:
    path = Path(file_path)
    raw = path.read_text(encoding="utf-8")
    text = strip_boilerplate(raw)
    raw_title = _guess_title(text, path.name)
    display_name = clean_heading_title(raw_title) or filename_stem_from_path(path)
    return Document(
        page_content=text,
        metadata={
            "source": str(path.resolve()),
            "filename": path.name,
            "title": raw_title,
            "display_name": display_name,
            "corpus_folder": path.parent.name.replace("_", " "),
            "file_type": path.suffix.lstrip(".").lower(),
        },
    )


def filename_stem_from_path(path: Path) -> str:
    return path.stem.replace("_", " ")


def discover_document_paths(data_dir: Path | None = None) -> list[Path]:
    """All supported text files under the corpus directory (recursive)."""
    root = data_dir or GENERAL_DATA_DIR
    if not root.is_dir():
        return [DATA_PATH] if DATA_PATH.is_file() else []

    paths: list[Path] = []
    for path in sorted(root.rglob("*")):
        if not path.is_file():
            continue
        if path.name.startswith((".", "~$")):
            continue
        if path.suffix.lower() not in SUPPORTED_EXTENSIONS:
            continue
        paths.append(path.resolve())

    if paths:
        return paths
    return [DATA_PATH] if DATA_PATH.is_file() else []


def load_documents(data_dir: Path | None = None) -> list[Document]:
    paths = discover_document_paths(data_dir)
    if not paths:
        raise FileNotFoundError(
            f"No general RAG documents found under {data_dir or GENERAL_DATA_DIR}. "
            f"Add .md or .txt files, then rebuild: "
            "python -m terramind.rag.general.cli --reset"
        )
    return [load_document(p) for p in paths]
