"""Resolve repository roots and paths used in lint diagnostics."""

from pathlib import Path


def repository_root(start: Path) -> Path | None:
    """Handle repository root."""
    for directory in (start, *start.parents):
        if (directory / ".git").exists():
            return directory
    return None


def relative_path(target: Path, root: Path) -> str:
    """Handle relative path."""
    try:
        return str(target.relative_to(root))
    except ValueError:
        return str(target)
