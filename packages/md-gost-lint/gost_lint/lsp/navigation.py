"""Resolve declarations and references within a single manifest."""

from collections.abc import Iterator

from lsprotocol import types
from pygls.workspace.position_codec import PositionCodec

from gost_lint.lsp.headings import headings
from gost_lint.lsp.marks import Declaration, Mark
from gost_lint.lsp.section_links import section_uses
from gost_lint.lsp.titles import title_for
from gost_lint.markdown import Document
from gost_lint.markdown.refs import LabelSpan


def declaration_marks(documents: list[Document]) -> Iterator[Declaration]:
    """Handle declaration marks."""
    for document in documents:
        for span, block in document.definition_spans():
            yield document, Mark.object_label(span), title_for(document, block)
    yield from headings(documents)


def reference_marks(document: Document) -> Iterator[Mark]:
    """Handle reference marks."""
    yield from (Mark.object_label(span) for span in document.reference_spans())
    yield from section_uses(document)


def label_at(
    document: Document,
    position: types.Position,
    documents: list[Document],
) -> Mark | None:
    """Handle label at."""
    for mark in reference_marks(document):
        if mark.contains(position.line, position.character):
            return mark
    for target, mark, _ in declaration_marks(documents):
        if target.path == document.path and mark.contains(position.line, position.character):
            return mark
    return None


def key_range(doc: Document, span: LabelSpan, codec: PositionCodec) -> types.Range:
    """Handle key range."""
    start = types.Position(span.line, span.start)
    end = types.Position(span.line, span.end)
    return codec.range_to_client_units(doc.lines, types.Range(start, end))


def hover_title(docs: list[Document], key: Mark | str) -> str:
    """Handle hover title."""
    for _, mark, title in declaration_marks(docs):
        if isinstance(key, str):
            if not mark.section and mark.span.label == key:
                return title
        elif key.matches(mark):
            return title
    return ""


def key_locations(
    docs: list[Document],
    key: Mark,
    codec: PositionCodec,
    *,
    declarations: bool,
    uses: bool,
) -> list[types.Location]:
    """Handle key locations."""
    keys = [key]
    if key.section and uses:
        targets = (mark for _, mark, _ in declaration_marks(docs))
        keys = list(filter(key.matches, targets))
    return [
        types.Location(document.path.as_uri(), key_range(document, mark.span, codec))
        for document, mark in _marks(docs, declarations=declarations, uses=uses)
        if any(target.matches(mark) for target in keys)
    ]


def _marks(
    docs: list[Document],
    *,
    declarations: bool,
    uses: bool,
) -> Iterator[tuple[Document, Mark]]:
    if declarations:
        for document, mark, _ in declaration_marks(docs):
            yield document, mark
    if uses:
        for document in docs:
            for mark in reference_marks(document):
                yield document, mark
