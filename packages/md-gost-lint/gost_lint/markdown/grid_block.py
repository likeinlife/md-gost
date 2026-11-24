"""Parse grid tables from their source rows."""

from gost_lint.markdown.grid import parse_grid
from gost_lint.markdown.syntax import is_grid_line
from gost_lint.markdown.types import Block


def grid_block(lines: list[str], start: int) -> tuple[Block, int]:
    """Handle grid block."""
    end = start + 1
    while end < len(lines) and is_grid_line(lines[end]):
        end += 1
    body = lines[start:end]
    metadata = {"grid": parse_grid(body)}
    return Block("table", start + 1, end, body, metadata), end
