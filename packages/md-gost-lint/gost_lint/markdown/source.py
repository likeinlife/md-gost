"""A parsed source snapshot, including key ranges and code-point positions."""

from collections.abc import Iterator
from dataclasses import dataclass
from functools import cached_property
from pathlib import Path
from typing import Self

from gost_lint.markdown.parser import parse as parse_markdown
from gost_lint.markdown.prose import ProseMap
from gost_lint.markdown.refs import LabelSpan, declaration, line_key_spans
from gost_lint.markdown.syntax import source_lines
from gost_lint.markdown.types import Block
from gost_lint.paths import relative_path


@dataclass
class DocumentSource:
    """Represent Document Source."""

    path: Path
    rel: str
    text: str
    lines: list[str]
    blocks: list[Block]

    @classmethod
    def load(cls, path: Path, root: Path) -> Self:
        """Handle load."""
        return cls.from_text(path, root, path.read_text(encoding="utf-8"))

    @classmethod
    def from_text(cls, path: Path, root: Path, text: str) -> Self:
        """Build from text."""
        rel = relative_path(path, root)
        return cls(path, rel, text, source_lines(text), parse_markdown(text))

    def definition_spans(self) -> Iterator[tuple[LabelSpan, Block]]:
        """Handle definition spans."""
        for block in self.blocks:
            if self.is_prose_position(block.start - 1, 0):
                span = declaration(block)
                if span is not None:
                    yield span, block

    def reference_spans(self) -> Iterator[LabelSpan]:
        """Handle reference spans."""
        for number, line in enumerate(self.lines):
            for span in line_key_spans(line, number):
                if self.is_prose_position(number, span.start):
                    yield span

    def is_prose_position(self, line: int, column: int) -> bool:
        """Check the insertion point in zero-based source coordinates."""
        return self.prose.visible(line, column)

    @cached_property
    def prose(self) -> ProseMap:
        """Handle prose."""
        return ProseMap(self.text, self.blocks)
