"""Honor optional EOF edits while retaining the document's original newline style."""

import re

from lsprotocol import types
from pygls.workspace.position_codec import PositionCodec

from gost_lint.markdown import Document

LINE_BREAK = re.compile(r"\r\n|\r|\n")


def _eof(doc: Document, codec: PositionCodec) -> types.Position:
    if doc.text.endswith(("\r", "\n")):
        return types.Position(len(doc.lines), 0)
    column = codec.client_num_units(doc.lines[-1])
    return types.Position(len(doc.lines) - 1, column)


def _first_trailing_row(lines: list[str]) -> int:
    first = len(lines)
    while first and not lines[first - 1].strip():
        first -= 1
    return first


def _newline(text: str) -> str:
    match = LINE_BREAK.search(text)
    return match[0] if match else "\n"


def ending_edit(
    doc: Document,
    codec: PositionCodec,
    options: types.FormattingOptions,
) -> types.TextEdit | None:
    """Handle ending edit."""
    if not doc.lines or not (options.insert_final_newline or options.trim_final_newlines):
        return None
    end = _eof(doc, codec)
    line = end.line
    last_line = doc.lines[line] if line < len(doc.lines) else ""
    if not doc.is_prose_position(line, len(last_line)):
        return None
    if options.trim_final_newlines and not doc.lines[-1].strip():
        first = _first_trailing_row(doc.lines)
        return types.TextEdit(types.Range(types.Position(first, 0), end), "")
    if options.insert_final_newline and line < len(doc.lines):
        return types.TextEdit(types.Range(end, end), _newline(doc.text))
    return None
