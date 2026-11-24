"""Clickable ranges and file destinations for references in the editor."""

from collections import defaultdict

from lsprotocol import types
from pygls.workspace.position_codec import PositionCodec

from gost_lint.lsp.marks import Declaration, Mark
from gost_lint.lsp.navigation import declaration_marks, key_range, reference_marks
from gost_lint.lsp.session import GostServer, document_book
from gost_lint.markdown import Document
from gost_lint.markdown.refs import LabelSpan


def _declarations(chapters: list[Document]) -> dict[str, list[Declaration]]:
    by_label: dict[str, list[Declaration]] = defaultdict(list)
    for declaration in declaration_marks(chapters):
        by_label[declaration[1].span.label].append(declaration)
    return by_label


def document_links(ls: GostServer, request: types.DocumentLinkParams) -> list[types.DocumentLink]:
    """Handle document links."""
    context = document_book(ls, request.text_document.uri)
    if context is None:
        return []
    document, book = context
    return _links(document, _declarations(book.work.docs), ls.workspace.position_codec)


def _links(
    document: Document,
    by_label: dict[str, list[Declaration]],
    codec: PositionCodec,
) -> list[types.DocumentLink]:
    links: list[types.DocumentLink] = []
    for use in reference_marks(document):
        uri = _destination(use, by_label.get(use.span.label, []), codec)
        if uri is not None:
            bounds = LabelSpan(use.span.label, use.span.line, *use.bounds)
            source = key_range(document, bounds, codec)
            links.append(types.DocumentLink(range=source, target=uri))
    return links


def _destination(use: Mark, candidates: list[Declaration], codec: PositionCodec) -> str | None:
    targets = [entry for entry in candidates if use.matches(entry[1])]
    if len(targets) != 1:
        return None
    chapter, mark, _ = targets[0]
    start = key_range(chapter, mark.span, codec).start
    return _position_uri(chapter.path.as_uri(), start)


def _position_uri(uri: str, start: types.Position) -> str:
    # Editors open file links at one-based line and column numbers.
    line, column = start.line + 1, start.character + 1
    return f"{uri}#{line},{column}"
