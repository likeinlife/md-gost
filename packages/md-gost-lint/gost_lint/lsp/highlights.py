"""Source spans for GOST labels and the metadata on Markdown blocks."""

import re
from collections.abc import Iterator
from dataclasses import dataclass

from gost_lint.lsp.headings import ATTRIBUTES
from gost_lint.lsp.navigation import declaration_marks, reference_marks
from gost_lint.markdown import Block, Document
from gost_lint.markdown.refs import LabelSpan
from gost_lint.markdown.syntax import FENCE, IMAGE

LABEL = "enumMember"
LANGUAGE = "type"
PROPERTY = "property"
ATTRIBUTE = re.compile(
    r""""(?:\\.|[^"\\])*"|'(?:\\.|[^'\\])*'|"""
    r"(?<![^\s{])(?:(?P<language>[.=][\w+#-]+)|(?P<property>[\w:-]+)(?=\s*=))",
)
BARE_LANGUAGE = re.compile(r"\s*(?P<language>[\w+#-]+)\s*$")
FENCED = frozenset(("listing", "diagram", "code"))


@dataclass(frozen=True, order=True)
class Highlight:
    """Represent Highlight."""

    line: int
    start: int
    end: int
    kind: str
    declared: bool = False

    @classmethod
    def label(cls, span: LabelSpan, *, declared: bool = False) -> "Highlight":
        """Handle label."""
        return cls(span.line, span.start - 1, span.end, LABEL, declared)


def _metadata(block: Block) -> Iterator[Highlight]:
    line = block.lines[0]
    number = block.start - 1
    if block.kind in FENCED:
        yield from _fence(line, number)
        return
    if block.kind == "heading":
        match, group = ATTRIBUTES.search(line.rstrip()), "body"
    elif block.kind == "image":
        match, group = IMAGE.match(line), "attrs"
    else:
        return
    if match and match[group]:
        yield from _attributes(line, number, match.span(group))


def _fence(line: str, number: int) -> Iterator[Highlight]:
    fence = FENCE.match(line)
    if fence is None:
        message = "fence line does not match"
        raise ValueError(message)
    language = BARE_LANGUAGE.fullmatch(line, fence.start("info"))
    if language:
        yield Highlight(number, *language.span("language"), LANGUAGE)
    elif fence["info"].lstrip().startswith("{"):
        yield from _attributes(line, number, fence.span("info"))


def _attributes(line: str, number: int, bounds: tuple[int, int]) -> Iterator[Highlight]:
    for match in ATTRIBUTE.finditer(line, *bounds):
        if match.lastgroup:
            kind = LANGUAGE if match.lastgroup == "language" else PROPERTY
            yield Highlight(number, match.start(), match.end(), kind)


def highlights(document: Document) -> Iterator[Highlight]:
    """Handle highlights."""
    for _, mark, _ in declaration_marks([document]):
        span = mark.span
        # Automatically generated heading IDs have no literal token in the source.
        line = document.lines[span.line]
        if line[span.start - 1] == "#":
            yield Highlight.label(span, declared=True)
    for mark in reference_marks(document):
        yield Highlight.label(mark.span)
    for block in document.blocks:
        if document.is_prose_position(block.start - 1, 0):
            yield from _metadata(block)
