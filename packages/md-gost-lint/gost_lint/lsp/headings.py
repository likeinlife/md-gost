"""Index ATX headings in manifest order, including Pandoc's automatic identifiers."""

import re
from collections.abc import Iterator
from typing import NoReturn

from gost_lint.lsp.identifiers import automatic_id
from gost_lint.lsp.marks import Declaration, Mark
from gost_lint.markdown import Block, Document
from gost_lint.markdown.metadata import QUOTED_ATTRIBUTE
from gost_lint.markdown.refs import LabelSpan
from gost_lint.markdown.syntax import HEADING

ATTRIBUTES = re.compile(r"\s*\{(?=[.#-]|[\w:-]+=)(?P<body>(?:[^{}'\"]|\"[^\"]*\"|'[^']*')*)\}$")
IDENTIFIER = re.compile(r"(?:^|\s)#(?P<key>[^\s{}]+)")


def _blank(match: re.Match[str]) -> str:
    return " " * len(match[0])


def _attribute_id(attributes: re.Match[str], number: int) -> LabelSpan | None:
    unquoted = QUOTED_ATTRIBUTE.sub(_blank, attributes["body"])
    match = IDENTIFIER.search(unquoted)
    if match is None:
        return None
    offset = attributes.start("body")
    start, end = match.span("key")
    return LabelSpan(match["key"], number, offset + start, offset + end)


def _invalid(text: str) -> NoReturn:
    raise ValueError(text)


def _heading_span(block: Block, used: set[str]) -> tuple[LabelSpan, str]:
    heading = HEADING.match(block.lines[0])
    if heading is None:
        _invalid("heading line does not match")
    start = heading.start("text")
    attributes = ATTRIBUTES.search(heading.string, start, heading.end("text"))
    title = heading["text"]
    if attributes:
        title = heading.string[start : attributes.start()]
    title = re.sub(r"\s+#+$", "", title).rstrip()
    span = _attribute_id(attributes, block.start - 1) if attributes else None
    if span is None:
        span = _automatic_span(title, block.start - 1, start, used)
    used.add(span.label)
    return span, title


def _automatic_span(title: str, number: int, start: int, used: set[str]) -> LabelSpan:
    return LabelSpan(automatic_id(title, used), number, start, start + len(title))


def headings(documents: list[Document]) -> Iterator[Declaration]:
    """Handle headings."""
    used: set[str] = set()
    for document in documents:
        for block in document.of_kind("heading"):
            if document.is_prose_position(block.start - 1, 0):
                yield _heading(document, block, used)


def _heading(document: Document, block: Block, used: set[str]) -> Declaration:
    span, title = _heading_span(block, used)
    bounds = (0, len(block.lines[0]))
    mark = Mark(span, bounds, section=True, chapter=document.path)
    return document, mark, title
