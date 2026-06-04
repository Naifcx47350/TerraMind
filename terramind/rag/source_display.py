"""
Human-readable source labels for the chat UI.

The API sends { title, source, section }; the website shows `title` only.
Extend resolve_source_title() per pipeline as catalogs and corpora grow.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any, Literal

PipelineKind = Literal["general", "product"]

_MARKDOWN_NOISE = re.compile(r"\*+|`+")


def clean_heading_title(raw: str | None) -> str:
    if not raw:
        return ""
    text = _MARKDOWN_NOISE.sub("", str(raw)).strip()
    return re.sub(r"\s+", " ", text)


def corpus_folder_name(source_path: str | Path | None) -> str:
    """Parent folder of the file (e.g. text, Documents) — no extension, no full path."""
    if not source_path:
        return "Documents"
    parent = Path(source_path).parent.name
    if parent in ("", ".", ".."):
        return Path(source_path).stem.replace("_", " ")
    return parent.replace("_", " ")


def filename_stem(source_path: str | Path | None) -> str:
    if not source_path:
        return "Document"
    return Path(source_path).stem.replace("_", " ")


def _looks_like_publication_title(title: str) -> bool:
    """Heuristic: prefer full paper/manual titles over short filenames."""
    if len(title) < 15:
        return False
    lowered = title.lower()
    if lowered in ("document", "untitled", "readme"):
        return False
    return True


def resolve_source_title(
    pipeline: PipelineKind,
    metadata: dict[str, Any],
) -> str:
    """
    Label shown in the UI source chips.

    general — full research/manual title when available, else corpus folder name.
    product — product name (catalog row); extend for catalog branding later.
    """
    if pipeline == "product":
        return _product_source_title(metadata)
    return _general_source_title(metadata)


def _general_source_title(metadata: dict[str, Any]) -> str:
    filename = metadata.get("filename")
    if filename:
        try:
            from terramind.rag.general.config import display_name_for_file

            mapped = display_name_for_file(str(filename))
            if mapped:
                return mapped
        except ImportError:
            pass

    if metadata.get("display_name"):
        return str(metadata["display_name"])

    doc_title = clean_heading_title(metadata.get("title"))
    if _looks_like_publication_title(doc_title):
        return doc_title

    if metadata.get("corpus_folder"):
        return str(metadata["corpus_folder"]).replace("_", " ")

    if metadata.get("source"):
        return corpus_folder_name(metadata["source"])

    if metadata.get("filename"):
        return filename_stem(metadata["filename"])

    return "Agriculture knowledge"


def _product_source_title(metadata: dict[str, Any]) -> str:
    # TODO: catalog display name from settings (e.g. client catalog title).
    name = metadata.get("product_name") or metadata.get("display_name")
    if name:
        return str(name).strip()
    if metadata.get("catalog_label"):
        return str(metadata["catalog_label"])
    if metadata.get("source"):
        return corpus_folder_name(metadata["source"])
    return "Product catalog"


def source_entry_from_chunk(
    pipeline: PipelineKind,
    metadata: dict[str, Any],
    *,
    section: str | None = None,
) -> dict[str, str | None]:
    """Build one API SourceOut-compatible dict."""
    path = metadata.get("source")
    return {
        "title": resolve_source_title(pipeline, metadata),
        "source": (
            metadata.get("corpus_folder")
            or (corpus_folder_name(path) if path else None)
            or ("product_catalog" if pipeline == "product" else "documents")
        ),
        "section": clean_heading_title(section) if section else None,
    }


def dedupe_key(pipeline: PipelineKind, metadata: dict[str, Any]) -> str:
    """One chip per document (general) or per product (catalog)."""
    if pipeline == "product":
        return f"{metadata.get('product_id', '')}|{metadata.get('product_name', '')}"
    return str(metadata.get("source") or metadata.get("filename") or metadata.get("title"))
