"""Normalize and clean text before chunking."""

import re


def clean_text(text: str) -> str:
    """Collapse extra whitespace and strip lines."""
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    lines = [line.strip() for line in text.split("\n")]
    text = "\n".join(line for line in lines if line)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()
