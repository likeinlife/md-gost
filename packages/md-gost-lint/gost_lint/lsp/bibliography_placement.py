"""Choose the end of the bibliography inside a chapter and preserve its line endings."""

import re
from dataclasses import dataclass

from lsprotocol import types
from pygls.workspace.position_codec import PositionCodec

from gost_lint.lsp.headings import ATTRIBUTES
from gost_lint.markdown import Block, Document

SECTION = re.compile(
    r"(?:\d+[.\d]*\s+)?(?:(?:список|перечень)\s+(?:(?:использованн\w+|библиографических)\s+)?"
    r"(?:источников|литературы|ссылок|информационных ресурсов)|источники|литература|библиография)",
    re.IGNORECASE,
)
DESCRIPTION = "Описание источника"


@dataclass(frozen=True)
class EntryPosition:
    """Represent Entry Position."""

    point: types.Position
    before: int
    after: int

    def entry(self, key: str, newline: str) -> types.TextEdit:
        """Handle entry."""
        marker = f"<!-- #{key} {DESCRIPTION} -->"
        body = newline * self.before + marker + newline * self.after
        return types.TextEdit(types.Range(self.point, self.point), body)

    def selection(self, key: str, codec: PositionCodec) -> types.Range:
        """Handle selection."""
        line = self.point.line + self.before
        start = codec.client_num_units(f"<!-- #{key} ")
        end = start + codec.client_num_units(DESCRIPTION)
        return types.Range(types.Position(line, start), types.Position(line, end))


def _after_bibliography(document: Document) -> int:
    entries = (block for _, block in document.definition_spans())
    markers = [block.end for block in entries if block.kind == "bib_marker"]
    if markers:
        return markers[-1]
    heading = bibliography_heading(document)
    return _section_end(heading, document) if heading else len(document.lines)


def bibliography_heading(document: Document) -> Block | None:
    """Handle bibliography heading."""
    for block in document.of_kind("heading"):
        title = ATTRIBUTES.sub("", block.meta["title"]).rstrip(" #")
        if SECTION.fullmatch(title) and document.is_prose_position(block.start - 1, 0):
            return block
    return None


def _section_end(heading: Block, document: Document) -> int:
    for block in document.of_kind("heading"):
        if block.start <= heading.end or block.level > heading.level:
            continue
        if document.is_prose_position(block.start - 1, 0):
            return block.start - 1
    return len(document.lines)


def entry_position(document: Document, codec: PositionCodec) -> EntryPosition:
    """Handle entry position."""
    line = _after_bibliography(document)
    if not line:
        return EntryPosition(types.Position(0, 0), 0, 1)
    missing_newline = not document.text.endswith(("\r", "\n"))
    if line == len(document.lines) and missing_newline:
        column = codec.client_num_units(document.lines[-1])
        return EntryPosition(types.Position(line - 1, column), 2, 1)
    return _between_lines(document.lines, line)


def _between_lines(lines: list[str], line: int) -> EntryPosition:
    before = 1 if lines[line - 1].strip() else 0
    following = lines[line] if line < len(lines) else ""
    after = 2 if following.strip() else 1
    return EntryPosition(types.Position(line, 0), before, after)


def document_newline(document: Document) -> str:
    """Handle document newline."""
    match = re.search(r"\r\n|\r|\n", document.text)
    return match[0] if match else "\n"
