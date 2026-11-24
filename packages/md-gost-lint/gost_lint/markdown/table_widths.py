"""Source display columns and Pandoc pipe table width selection."""

import re
import unicodedata

PANDOC_COLUMNS = 72
OUTER_PIPE = re.compile(r"(?<!\\)(?:\\\\)*\| *$")


def column_width(column: tuple[str, ...]) -> int:
    """Handle column width."""
    return max(map(text_width, column))


def pad_field(field: str, width: int) -> str:
    """Handle pad field."""
    return field + " " * (width - text_width(field))


def wide_table(lines: list[str]) -> bool:
    """Handle wide table."""
    return any(_row_width(line) > PANDOC_COLUMNS for line in lines)


def _row_width(line: str) -> int:
    # The reader counts a border at each end, including omitted outer pipes.
    source = line.lstrip(" ")
    missing = int(not source.startswith("|"))
    if OUTER_PIPE.search(source):
        return text_width(source.rstrip(" ")) + missing
    return text_width(source) + missing + 1


def text_width(text: str) -> int:
    """Handle text width."""
    return sum(map(_char_width, text))


def _char_width(char: str) -> int:
    if unicodedata.category(char) in {"Mn", "Me", "Cf"}:
        return 0
    return 2 if unicodedata.east_asian_width(char) in {"W", "F"} else 1
