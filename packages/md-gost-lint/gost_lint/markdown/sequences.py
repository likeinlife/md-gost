"""List and paragraph span detection."""

from gost_lint.markdown.grid import START as GRID_START
from gost_lint.markdown.syntax import FENCE, HEADING, LIST_ITEM, TABLE_ROW


def list_end(lines: list[str], start: int) -> int:
    """List end."""
    last = start
    position = start
    while position < len(lines):
        next_position = next_list_position(lines, position)
        if next_position is None:
            break
        last = next_position
        position = next_position + 1
    return last + 1


def next_list_position(lines: list[str], position: int) -> int | None:
    """Handle next list position."""
    line = lines[position]
    if line.strip():
        return position if continues_list(line) else None
    return list_continuation(lines, position + 1)


def next_content_line(lines: list[str], start: int) -> int:
    """Handle next content line."""
    while start < len(lines) and not lines[start].strip():
        start += 1
    return start


def list_continuation(lines: list[str], start: int) -> int | None:
    """List continuation."""
    next_item = next_content_line(lines, start)
    if next_item < len(lines) and continues_list(lines[next_item]):
        return next_item
    return None


def continues_list(line: str) -> bool:
    """Handle continues list."""
    return bool(LIST_ITEM.match(line) or line.startswith(("  ", "\t")))


def paragraph_end(lines: list[str], start: int) -> int:
    """Handle paragraph end."""
    end = start
    while (
        end < len(lines)
        and lines[end].strip()
        and not any(
            matcher(lines[end])
            for matcher in (
                HEADING.match,
                FENCE.match,
                TABLE_ROW.match,
                GRID_START.match,
                LIST_ITEM.match,
            )
        )
        and not lines[end].strip().startswith("<!--")
    ):
        end += 1
    return end
