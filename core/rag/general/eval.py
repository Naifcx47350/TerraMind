"""General RAG — corpus inspect and retrieval evaluation (no LLM)."""

from __future__ import annotations

import json
from pathlib import Path

from langchain_chroma import Chroma

from core.rag.general.config import (
    EVAL_QUESTIONS_PATH,
    INSPECT_MIN_CHARS,
    INSPECT_MIN_CHARS_TEXT,
    INSPECT_PREVIEW_CHARS,
)
from core.rag.general.load import discover_document_paths, load_document
from core.rag.general.retrieve import retrieve_chunks

STALE_INDEX_HINT = (
    "Rebuild the index: python -m core.rag.general.cli --reset"
)


def inspect_corpus(*, dry_load: bool = False) -> int:
    """Print per-file char counts and previews. Returns count of low-quality files."""
    _ = dry_load
    paths = discover_document_paths()
    print(f"Discovered {len(paths)} file(s)\n")
    warnings = 0
    for path in paths:
        doc = load_document(path)
        chars = len(doc.page_content)
        preview = doc.page_content[:INSPECT_PREVIEW_CHARS]

        min_chars = (
            INSPECT_MIN_CHARS_TEXT
            if path.suffix.lower() in {".txt", ".md", ".markdown"}
            else INSPECT_MIN_CHARS
        )
        status = "OK"
        if chars < min_chars:
            status = "LOW (check PDF extraction)"
            warnings += 1
        print(f"--- {path.name} ---")
        print(f"  chars: {chars:,}  [{status}]")
        print(f"  topic: {doc.metadata.get('corpus_topic')}  id: {doc.metadata.get('document_id')}")
        print(f"  preview:\n{preview}\n")
    if warnings:
        print(f"Warning: {warnings} file(s) below {INSPECT_MIN_CHARS:,} characters.")
    return warnings


def warn_if_stale_index(db: Chroma) -> bool:
    """True if the index contains filenames no longer in the discovered corpus."""
    expected = {p.name for p in discover_document_paths()}
    result = db._collection.get(include=["metadatas"])
    metas = result.get("metadatas") or []
    indexed = {
        m.get("filename")
        for m in metas
        if isinstance(m, dict) and m.get("filename")
    }
    stale = sorted(indexed - expected)
    if not stale:
        return False
    print(
        "WARNING: Chroma index still has chunks from files not in the current corpus:"
    )
    for name in stale:
        print(f"  - {name}")
    print(STALE_INDEX_HINT)
    print()
    return True


def load_eval_questions(path: Path | None = None) -> list[dict]:
    eval_path = path or EVAL_QUESTIONS_PATH
    data = json.loads(eval_path.read_text(encoding="utf-8"))
    if not isinstance(data, list):
        raise ValueError(f"Expected JSON array in {eval_path}")
    return data


def run_retrieval_eval(db: Chroma, questions_path: Path | None = None) -> dict:
    """Run golden questions; report hit rate (expected filename in top-k)."""
    warn_if_stale_index(db)
    questions = load_eval_questions(questions_path)
    hits = 0
    total = len(questions)

    print(f"Retrieval eval: {total} questions (k=6)\n")
    for row in questions:
        q = row["question"]
        expected = row.get("expected_filename", "")
        retrieved = retrieve_chunks(db, q)
        found_files = {d.metadata.get("filename") for d in retrieved}
        ok = expected in found_files
        if ok:
            hits += 1
        mark = "PASS" if ok else "MISS"
        print(f"[{mark}] {row.get('id', '?')} | expected: {expected}")
        print(f"  Q: {q[:90]}{'...' if len(q) > 90 else ''}")
        for i, doc in enumerate(retrieved[:3], start=1):
            sec = doc.metadata.get("h2") or doc.metadata.get("h1") or ""
            print(f"    {i}. {doc.metadata.get('filename')} | {sec[:50]}")
        if not ok and retrieved:
            print(f"    got: {', '.join(sorted(found_files))}")
        print()

    rate = (hits / total * 100) if total else 0.0
    print(f"Hit rate: {hits}/{total} ({rate:.0f}%) — target >= 80%")
    return {"hits": hits, "total": total, "rate_pct": rate}
