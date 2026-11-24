"""Symbols, source ranges and hit areas used in Markdown navigation."""

from dataclasses import dataclass
from pathlib import Path

from gost_lint.markdown import Document
from gost_lint.markdown.refs import LabelSpan


@dataclass(frozen=True)
class Mark:
    """Represent Mark."""

    span: LabelSpan
    bounds: tuple[int, int]
    section: bool = False
    chapter: Path | None = None

    @classmethod
    def object_label(cls, span: LabelSpan) -> "Mark":
        """Handle object label."""
        return cls(span, (span.start - 1, span.end))

    def matches(self, other: "Mark") -> bool:
        """Handle matches."""
        same_chapter = (
            self.chapter is None or other.chapter is None or self.chapter == other.chapter
        )
        return (
            self.section == other.section and self.span.label == other.span.label and same_chapter
        )

    def hover_span(self, column: int) -> LabelSpan:
        """Handle hover span."""
        if self.span.start <= column < self.span.end:
            return self.span
        return LabelSpan(self.span.label, self.span.line, *self.bounds)

    def contains(self, line: int, column: int) -> bool:
        """Handle contains."""
        start, end = self.bounds
        return self.span.line == line and start <= column < end


Declaration = tuple[Document, Mark, str]
