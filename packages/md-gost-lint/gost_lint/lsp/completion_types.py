"""Editor-independent completion edits on a single source line."""

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class EditorOptions:
    """Represent Editor Options."""

    snippets: bool
    pandoc_languages: frozenset[str] = frozenset()
    workspace_root: Path | None = None


@dataclass(frozen=True)
class Suggestion:
    """Represent Suggestion."""

    label: str
    detail: str
    text: str
    start: int
    end: int
    snippet: bool = False
    filter_text: str | None = None
