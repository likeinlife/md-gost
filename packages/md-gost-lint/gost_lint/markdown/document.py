"""Document model for the Markdown dialect md-to-gost consumes."""

from collections.abc import Iterator
from functools import cached_property

from gost_lint.markdown.format_scope import FormatScope
from gost_lint.markdown.source import DocumentSource
from gost_lint.markdown.types import Block, Section


class Document(DocumentSource):
    """Represent Document."""

    @cached_property
    def format_scope(self) -> FormatScope:
        """Format scope."""
        return FormatScope(self)

    def of_kind(self, *kinds: str) -> list[Block]:
        """Handle of kind."""
        return [block for block in self.blocks if block.kind in kinds]

    def definitions(self) -> list[tuple[str, Block]]:
        """Return each declared figure, table, equation, listing, and citation label."""
        return [(span.label, block) for span, block in self.definition_spans()]

    def references(self) -> list[tuple[str, int, int]]:
        """Return (label, line, column) for each reference outside code blocks."""
        return [span.lint_location() for span in self.reference_spans()]

    def sections(self) -> list[Section]:
        """Return each heading and its body up to the next heading."""
        positions = _heading_positions(self.blocks)
        boundaries = [*positions[1:], len(self.blocks)]
        return [
            _section(self.blocks, heading_index, next_heading)
            for heading_index, next_heading in zip(positions, boundaries, strict=False)
        ]

    def main_sections(self) -> Iterator[Section]:
        """Return the sections of the main text, skipping appendices and their subsections."""
        in_appendix = False
        for heading, body in self.sections():
            if heading.level == 1:
                in_appendix = heading.is_appendix
            if not in_appendix:
                yield heading, body

    def is_bibliography(self) -> bool:
        """Check whether this is a references file with no regular prose."""
        kinds = {block.kind for block in self.blocks}
        return bool(kinds) and kinds <= {"bib_marker", "comment"}


def _heading_positions(blocks: list[Block]) -> list[int]:
    return [index for index, block in enumerate(blocks) if block.kind == "heading"]


def _section(blocks: list[Block], start: int, end: int) -> Section:
    return blocks[start], blocks[start + 1 : end]
