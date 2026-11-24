"""Build a sequence of typed blocks from Markdown text."""

from gost_lint.markdown import syntax
from gost_lint.markdown.blocks import (
    formula_block,
    heading_block,
    image_block,
    marker_block,
    table_block,
)
from gost_lint.markdown.fences import fence_block
from gost_lint.markdown.grid import START as GRID_START
from gost_lint.markdown.grid_block import grid_block
from gost_lint.markdown.pipe_rows import table_header
from gost_lint.markdown.sequences import list_end, paragraph_end
from gost_lint.markdown.types import Block


def _block_at(lines: list[str], start: int) -> tuple[Block | None, int]:
    line = lines[start]
    number = start + 1
    block = _single_line_block(line, number)
    if block is not None:
        return block, start + 1
    if line.lstrip().startswith("<!--"):
        end = _comment_end(lines, start)
        return Block("comment", number, end, lines[start:end]), end
    block, next_position = _compound_block(lines, start)
    if block is not None:
        return block, next_position
    end = paragraph_end(lines, start)
    return Block("paragraph", number, end, lines[start:end]), end


def _comment_end(lines: list[str], start: int) -> int:
    for position, line in enumerate(lines[start:], start):
        if "-->" in line:
            return position + 1
    return len(lines)


def _single_line_block(line: str, number: int) -> Block | None:
    for matcher, kind in (
        (syntax.TBL_MARKER, "table_marker"),
        (syntax.EQ_MARKER, "eq_marker"),
        (syntax.BIB_MARKER, "bib_marker"),
    ):
        match = matcher.match(line.strip())
        if match:
            return marker_block(line, number, kind, match)
    if syntax.COMMENT.match(line.strip()):
        return Block("comment", number, number, [line])
    if syntax.IMAGE.match(line):
        return image_block(line, number)
    return None


def _compound_block(lines: list[str], start: int) -> tuple[Block | None, int]:
    line = lines[start]
    number = start + 1
    if syntax.FORMULA_FENCE.match(line):
        return formula_block(lines, start)
    if GRID_START.match(line):
        return grid_block(lines, start)
    if syntax.TABLE_ROW.match(line) or table_header(lines, start):
        return table_block(lines, start)
    if syntax.LIST_ITEM.match(line):
        end = list_end(lines, start)
        return Block("list", number, end, lines[start:end]), end
    return None, start


def parse(text: str) -> list[Block]:
    """Split Markdown source into a flat list of typed blocks."""
    lines = syntax.source_lines(text)
    blocks: list[Block] = []
    position = 0
    while position < len(lines):
        if not lines[position].strip():
            position += 1
            continue
        if syntax.FENCE.match(lines[position]):
            block, position = fence_block(lines, position)
        elif syntax.HEADING.match(lines[position]):
            block = heading_block(lines[position], position + 1)
            position += 1
        else:
            block, position = _block_at(lines, position)
        if block is not None:
            blocks.append(block)
    return blocks
