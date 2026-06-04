"""General RAG — load PDF, markdown, and text documents."""

import re
from pathlib import Path

from langchain_core.documents import Document
from pypdf import PdfReader

from terramind.rag.general.config import (
    EXCLUDED_FILENAMES,
    GENERAL_DOCUMENTS_DIR,
    GENERAL_SAMPLE_DIR,
    GENERAL_TEXT_DIR,
    SAMPLE_FILE_ALLOWLIST,
    PDF_EXTENSIONS,
    TEXT_EXTENSIONS,
    display_name_for_file,
    document_id_for_path,
    topic_for_filename,
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
    mapped = display_name_for_file(filename)
    if mapped:
        return mapped
    for line in text.splitlines():
        line = line.strip()
        if line.startswith("# "):
            return line.lstrip("# ").strip()
        if line.lower().startswith("title:"):
            return line.split(":", 1)[1].strip()
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


def _read_pdf_text(path: Path) -> str:
    reader = PdfReader(str(path))
    parts: list[str] = []
    for page in reader.pages:
        text = page.extract_text() or ""
        if text.strip():
            parts.append(text)
    return "\n\n".join(parts)


def _document_metadata(path: Path, raw_title: str) -> dict:
    mapped = display_name_for_file(path.name)
    display_name = clean_heading_title(mapped or raw_title) or filename_stem_from_path(path)
    return {
        "source": str(path.resolve()),
        "filename": path.name,
        "document_id": document_id_for_path(path),
        "corpus_topic": topic_for_filename(path.name),
        "title": raw_title,
        "display_name": display_name,
        "corpus_folder": path.parent.name.replace("_", " "),
        "file_type": path.suffix.lstrip(".").lower(),
    }


def load_document(file_path: str | Path) -> Document:
    path = Path(file_path)
    suffix = path.suffix.lower()

    if suffix in PDF_EXTENSIONS:
        raw = _read_pdf_text(path)
        if not raw.strip():
            raise ValueError(f"No extractable text in PDF: {path}")
        text = strip_boilerplate(raw)
        raw_title = display_name_for_file(path.name) or filename_stem_from_path(path)
    else:
        raw = path.read_text(encoding="utf-8")
        text = strip_boilerplate(raw)
        raw_title = _guess_title(text, path.name)

    return Document(
        page_content=text,
        metadata=_document_metadata(path, raw_title),
    )


def filename_stem_from_path(path: Path) -> str:
    return path.stem.replace("_", " ")


def _collect_from_dir(
    root: Path,
    extensions: set[str],
    *,
    sample_allowlist: frozenset[str] | None = None,
) -> list[Path]:
    if not root.is_dir():
        return []
    paths: list[Path] = []
    for path in sorted(root.rglob("*")):
        if not path.is_file():
            continue
        if path.name.startswith((".", "~$")):
            continue
        if path.name.upper() == "README.MD":
            continue
        if path.name in EXCLUDED_FILENAMES:
            continue
        if sample_allowlist is not None and path.name not in sample_allowlist:
            continue
        if path.suffix.lower() not in extensions:
            continue
        paths.append(path.resolve())
    return paths


def discover_document_paths() -> list[Path]:
    """
    PDFs and text from data/raw/documents/; optional .md/.txt from data/raw/text/.
    Product Excel in text/ is excluded.
    """
    paths: list[Path] = []
    paths.extend(_collect_from_dir(GENERAL_DOCUMENTS_DIR, TEXT_EXTENSIONS | PDF_EXTENSIONS))
    paths.extend(_collect_from_dir(GENERAL_TEXT_DIR, TEXT_EXTENSIONS))
    paths.extend(
        _collect_from_dir(
            GENERAL_SAMPLE_DIR,
            TEXT_EXTENSIONS,
            sample_allowlist=SAMPLE_FILE_ALLOWLIST,
        )
    )

    # Stable order, one path per file
    unique = sorted({str(p): p for p in paths}.values(), key=lambda p: str(p).lower())
    return list(unique)


def load_documents() -> list[Document]:
    paths = discover_document_paths()
    if not paths:
        raise FileNotFoundError(
            f"No general RAG documents found. Add PDF or .md files under "
            f"{GENERAL_DOCUMENTS_DIR} (see data/raw/documents/README.md), then rebuild:\n"
            "  python -m terramind.rag.general.cli --reset"
        )

    docs: list[Document] = []
    errors: list[str] = []
    for path in paths:
        try:
            docs.append(load_document(path))
            print(f"  Loaded: {path.name} ({len(docs[-1].page_content):,} chars)")
        except Exception as e:
            errors.append(f"{path.name}: {e}")

    if not docs:
        raise FileNotFoundError(
            "No documents could be loaded.\n" + "\n".join(errors)
        )
    if errors:
        print("Warnings:")
        for err in errors:
            print(f"  - {err}")
    return docs
