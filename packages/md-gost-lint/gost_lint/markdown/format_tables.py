"""Format source table layout without changing column alignment or Pandoc widths."""

from collections.abc import Iterable

from gost_lint.markdown.format_grid import format_grid
from gost_lint.markdown.pipe_rows import AMBIGUOUS, SEPARATOR
from gost_lint.markdown.table_widths import column_width, pad_field, wide_table
from gost_lint.markdown.types import Block


def format_table(block: Block) -> list[str]:
    """Format table."""
    if "grid" in block.meta:
        return format_grid(block)
    rows: list[list[str]] = block.meta.get("rows", [])
    if not _regular_table(rows) or any(map(_ambiguous_row, block.lines)):
        return block.lines
    return _align(rows, block.lines)


def _align(rows: list[list[str]], source: list[str]) -> list[str]:
    indent = _indentation(source[0])
    widths = list(map(column_width, zip(*rows, strict=True)))
    aligned = [_render(indent, map(pad_field, row, widths)) for row in rows]
    # Above --columns Pandoc derives relative widths from delimiter dash counts.
    # Padding can push a previously narrow table across that same threshold.
    wide = wide_table(source)
    if wide_table(aligned) == wide:
        return aligned
    compact = [_render(indent, row) for row in rows]
    return compact if wide_table(compact) == wide else source


def _regular_table(rows: list[list[str]]) -> bool:
    header_and_divider = 2
    if len(rows) < header_and_divider:
        return False
    divider = rows[1]
    count = len(divider)
    rectangular = all(len(row) == count for row in rows)
    return rectangular and all(map(SEPARATOR.fullmatch, divider))


def _ambiguous_row(line: str) -> bool:
    return "\t" in line or AMBIGUOUS.search(line) is not None


def _render(indent: str, fields: Iterable[str]) -> str:
    body = " | ".join(fields)
    return f"{indent}| {body} |"


def _indentation(line: str) -> str:
    return " " * (len(line) - len(line.lstrip(" ")))
