"""Publish semantic colors for GOST markup on top of the client's Markdown grammar."""

from collections.abc import Iterator

from lsprotocol import types
from pygls.workspace.position_codec import PositionCodec

from gost_lint.lsp.highlights import LABEL, LANGUAGE, PROPERTY, Highlight, highlights
from gost_lint.lsp.session import GostServer, document_book
from gost_lint.markdown import Document

LEGEND = types.SemanticTokensLegend(
    token_types=[LABEL, LANGUAGE, PROPERTY],
    token_modifiers=["declaration"],
)


def _positions(
    document: Document,
    codec: PositionCodec,
    requested: types.Range | None,
) -> Iterator[tuple[types.Range, Highlight]]:
    previous_end = types.Position(0, 0)
    for token in sorted(highlights(document)):
        start = types.Position(token.line, token.start)
        if previous_end > start:
            continue
        end = types.Position(token.line, token.end)
        previous_end = end
        bounds = codec.range_to_client_units(document.lines, types.Range(start, end))
        if requested is None or _overlaps(bounds, requested):
            yield bounds, token


def _overlaps(bounds: types.Range, requested: types.Range) -> bool:
    return requested.end > bounds.start and bounds.end > requested.start


def _relative(bounds: types.Range, token: Highlight, previous: types.Position) -> tuple[int, ...]:
    start = bounds.start
    line = start.line - previous.line
    column = start.character if line else start.character - previous.character
    length = bounds.end.character - start.character
    kind = LEGEND.token_types.index(token.kind)
    return line, column, length, kind, int(token.declared)


def _tokens(ls: GostServer, uri: str, requested: types.Range | None) -> types.SemanticTokens:
    context = document_book(ls, uri)
    encoded: list[int] = []
    if context:
        previous = types.Position(0, 0)
        for bounds, token in _positions(context[0], ls.workspace.position_codec, requested):
            encoded.extend(_relative(bounds, token, previous))
            previous = bounds.start
    return types.SemanticTokens(data=encoded)


def _full(ls: GostServer, request: types.SemanticTokensParams) -> types.SemanticTokens:
    return _tokens(ls, request.text_document.uri, None)


def _range(ls: GostServer, request: types.SemanticTokensRangeParams) -> types.SemanticTokens:
    return _tokens(ls, request.text_document.uri, request.range)


def register_semantic_tokens(server: GostServer) -> None:
    """Handle register semantic tokens."""
    server.feature(types.TEXT_DOCUMENT_SEMANTIC_TOKENS_FULL, LEGEND)(_full)
    server.feature(types.TEXT_DOCUMENT_SEMANTIC_TOKENS_RANGE, LEGEND)(_range)
