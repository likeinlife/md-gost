"""Return local edits for GOST Markdown in the editor's current position encoding."""

from collections.abc import Iterator
from os.path import commonprefix

from lsprotocol import types
from pygls.workspace.position_codec import PositionCodec

from gost_lint.lsp.format_endings import ending_edit
from gost_lint.lsp.session import GostServer, open_buffer
from gost_lint.lsp.workspace_edits import repair_edit
from gost_lint.markdown import Document
from gost_lint.markdown.format_tables import format_table
from gost_lint.markdown.types import Block
from gost_lint.spacing import spaces

Selection = types.Range | None


def _row_edit(line: int, before: str, after: str, codec: PositionCodec) -> types.TextEdit:
    prefix = commonprefix((before, after))
    start = types.Position(line, codec.client_num_units(prefix))
    end = types.Position(line, codec.client_num_units(before))
    replacement = after[len(prefix) :]
    return types.TextEdit(types.Range(start, end), replacement)


def _touches(block: Block, selection: Selection) -> bool:
    if selection is None:
        return True
    start = block.start - 1
    if selection.start == selection.end:
        return start <= selection.start.line < block.end
    first = types.Position(start, 0)
    return selection.start.line < block.end and first < selection.end


def _tables(doc: Document, codec: PositionCodec, selection: Selection) -> Iterator[types.TextEdit]:
    for block in doc.of_kind("table"):
        if not _touches(block, selection) or not doc.format_scope.table_allowed(block):
            continue
        rows = zip(block.lines, format_table(block), strict=True)
        for line, (before, after) in enumerate(rows, block.start - 1):
            if before != after:
                yield _row_edit(line, before, after, codec)


def _prose(doc: Document, codec: PositionCodec) -> Iterator[types.TextEdit]:
    # Zed disables blanket trimming to preserve Markdown hard breaks. The GOST
    # spacing rules distinguish these from genuinely redundant trailing spaces.
    for repair in spaces(doc, doc.format_scope):
        yield repair_edit(doc, repair, codec)


def _edits(
    doc: Document,
    codec: PositionCodec,
    options: types.FormattingOptions,
    selection: Selection,
) -> list[types.TextEdit]:
    prose = _prose(doc, codec)
    edits = list(_tables(doc, codec, selection))
    if selection is None:
        tail = ending_edit(doc, codec, options)
        if tail:
            retained = tail.range.start
            edits.extend(edit for edit in prose if edit.range.end <= retained)
            edits.append(tail)
        else:
            edits.extend(prose)
    else:
        edits.extend(edit for edit in prose if _within(edit.range, selection))
    return sorted(edits, key=lambda edit: edit.range.start)


def _within(edit: types.Range, selection: types.Range) -> bool:
    return selection.start <= edit.start and edit.end <= selection.end


def formatting(
    server: GostServer,
    request: types.DocumentFormattingParams | types.DocumentRangeFormattingParams,
) -> list[types.TextEdit]:
    """Handle formatting."""
    buffer = open_buffer(server, request.text_document.uri)
    if buffer is None:
        return []
    selection = request.range if isinstance(request, types.DocumentRangeFormattingParams) else None
    return _edits(buffer.document, server.workspace.position_codec, request.options, selection)
