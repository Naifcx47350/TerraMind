#!/usr/bin/env python
"""Export general RAG answers for golden questions (optional LLM eval)."""

from __future__ import annotations

import sys
from datetime import datetime
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from core.rag.general.eval import load_eval_questions
from core.rag.general.pipeline import answer_with_rag, get_general_db


def main() -> None:
    questions = load_eval_questions()
    db = get_general_db()
    out_dir = REPO_ROOT / "data/eval/runs"
    out_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    out_path = out_dir / f"general_rag_answers_{stamp}.txt"

    lines: list[str] = []
    for row in questions:
        q = row["question"]
        result = answer_with_rag(db, q, generation_prompt=q)
        lines.append(f"=== {row.get('id', '?')} | expected: {row.get('expected_filename', '')} ===")
        lines.append(f"Q: {q}")
        lines.append(result["answer"] or "")
        lines.append("")

    out_path.write_text("\n".join(lines), encoding="utf-8")
    print(f"Wrote {len(questions)} answers to {out_path}")


if __name__ == "__main__":
    main()
