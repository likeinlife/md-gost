"""stdio entry point for the md-to-gost Markdown language server."""

from lsprotocol import types

from gost_lint.lsp.code_actions import register_code_actions
from gost_lint.lsp.completion import Suggestion, complete
from gost_lint.lsp.completion_types import EditorOptions
from gost_lint.lsp.document_links import document_links
from gost_lint.lsp.events import register_events
from gost_lint.lsp.formatting import formatting
from gost_lint.lsp.navigation import hover_title, key_locations, key_range, label_at
from gost_lint.lsp.semantic_tokens import register_semantic_tokens
from gost_lint.lsp.session import Cursor, GostServer

server = GostServer()
register_code_actions(server)
register_events(server)
server.feature(types.TEXT_DOCUMENT_FORMATTING)(formatting)
server.feature(types.TEXT_DOCUMENT_RANGE_FORMATTING)(formatting)
register_semantic_tokens(server)
server.feature(types.TEXT_DOCUMENT_DOCUMENT_LINK, types.DocumentLinkOptions())(document_links)
MARKUP_TRIGGERS = ("@", ":", "|", "#", "!", "[", "(", "/", "+")
FENCE_TRIGGERS = ("`", "~", "{", ".", '"', "'")
COMPLETION = types.CompletionOptions(trigger_characters=[*MARKUP_TRIGGERS, *FENCE_TRIGGERS])


def _snippets_supported() -> bool:
    text = server.client_capabilities.text_document
    capability = text.completion if text else None
    options = capability.completion_item if capability else None
    return bool(options and options.snippet_support)


def _completion_item(cursor: Cursor, suggestion: Suggestion) -> types.CompletionItem:
    line = cursor.position.line
    start = types.Position(line, suggestion.start)
    span = types.Range(start, types.Position(line, suggestion.end))
    edit = server.workspace.position_codec.range_to_client_units(cursor.document.lines, span)
    formats = types.InsertTextFormat
    return types.CompletionItem(
        label=suggestion.label,
        detail=suggestion.detail,
        filter_text=suggestion.filter_text,
        text_edit=types.TextEdit(edit, suggestion.text),
        insert_text_format=formats.Snippet if suggestion.snippet else formats.PlainText,
    )


@server.feature(types.TEXT_DOCUMENT_COMPLETION, COMPLETION)
def completion(request: types.CompletionParams) -> list[types.CompletionItem]:
    """Handle completion."""
    cursor = server.cursor(request.text_document.uri, request.position)
    if cursor is None:
        return []
    point = cursor.position
    options = EditorOptions(_snippets_supported(), server.pandoc_languages, cursor.book.root)
    suggestions = complete(cursor.document, cursor.book.work, point.line, point.character, options)
    return [_completion_item(cursor, suggestion) for suggestion in suggestions]


def _locations(cursor: Cursor | None, *, declarations: bool, uses: bool) -> list[types.Location]:
    if cursor is None:
        return []
    mark = label_at(cursor.document, cursor.position, cursor.book.work.docs)
    if mark is None:
        return []
    return key_locations(
        cursor.book.work.docs,
        mark,
        server.workspace.position_codec,
        declarations=declarations,
        uses=uses,
    )


@server.feature(types.TEXT_DOCUMENT_DEFINITION)
def definition(request: types.DefinitionParams) -> list[types.Location]:
    """Handle definition."""
    cursor = server.cursor(request.text_document.uri, request.position)
    return _locations(cursor, declarations=True, uses=False)


@server.feature(types.TEXT_DOCUMENT_REFERENCES)
def references(request: types.ReferenceParams) -> list[types.Location]:
    """Handle references."""
    cursor = server.cursor(request.text_document.uri, request.position)
    return _locations(cursor, declarations=request.context.include_declaration, uses=True)


@server.feature(types.TEXT_DOCUMENT_HOVER)
def hover(request: types.HoverParams) -> types.Hover | None:
    """Handle hover."""
    cursor = server.cursor(request.text_document.uri, request.position)
    if cursor is None:
        return None
    mark = label_at(cursor.document, cursor.position, cursor.book.work.docs)
    if mark is None:
        return None
    title = hover_title(cursor.book.work.docs, mark)
    if not title:
        return None
    span = mark.hover_span(cursor.position.character)
    return types.Hover(
        contents=types.MarkupContent(types.MarkupKind.PlainText, title),
        range=key_range(cursor.document, span, server.workspace.position_codec),
    )
