"""Small shared helpers."""

from pathlib import Path


def ensure_project_root_on_path():
    """Allow running scripts from repo root without installing the package."""
    import sys

    root = Path(__file__).resolve().parent.parent
    if str(root) not in sys.path:
        sys.path.insert(0, str(root))
