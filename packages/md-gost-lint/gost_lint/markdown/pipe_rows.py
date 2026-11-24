"""Read pipe table cells without splitting escaped pipes or Pandoc code spans."""

import re

from gost_lint.markdown.syntax import TABLE_ROW

PIPE = "|"
SEPARATOR = re.compile(r":?-+:?")
TOKEN = re.compile(r"\\.|`+(?!`)|\|")
BACKTICKS = re.compile(r"`+")
DELIMITERS = re.compile(r"[\s|:\-]+")
# Raw inline HTML and mathematics have their own delimiter rules.
AMBIGUOUS = re.compile(r"<[^>]*\||\$[^$]*\|[^$]*\$")


def cells(line: str) -> list[str]:
    """Handle cells."""
    source = line.strip(" \t")
    boundaries = _boundaries(source)
    if not boundaries:
        return [source]
    parts: list[str] = []
    start = int(boundaries[0] == 0)
    for position in boundaries:
        if position:
            parts.append(source[start:position].strip(" \t"))
        start = position + 1
    if start < len(source) or not parts:
        parts.append(source[start:].strip(" \t"))
    return parts


def _boundaries(source: str) -> list[int]:
    pipes: list[int] = []
    match = TOKEN.search(source)
    while match is not None:
        start = match.end()
        if match[0] == PIPE:
            pipes.append(match.start())
        elif match[0].startswith("`"):
            start = _code_end(source, match)
        match = TOKEN.search(source, start)
    return pipes


def _code_end(source: str, opening: re.Match[str]) -> int:
    for closing in BACKTICKS.finditer(source, opening.end()):
        if closing[0] == opening[0]:
            return closing.end()
    return opening.end()


def table_header(lines: list[str], start: int) -> bool:
    """Recognize a header without outer pipes only when its divider agrees."""
    if start + 1 >= len(lines) or PIPE not in lines[start]:
        return False
    divider = lines[start + 1]
    if PIPE not in divider or not DELIMITERS.fullmatch(divider):
        return False
    header = lines[start]
    if header.startswith(("    ", "\t", ">")) or not _body_row(header):
        return False
    marks = cells(divider)
    regular = len(marks) == len(cells(header))
    return regular and all(map(SEPARATOR.fullmatch, marks))


def table_end(lines: list[str], start: int) -> int:
    """Handle table end."""
    if not table_header(lines, start):
        end = start + 1
        while end < len(lines) and TABLE_ROW.match(lines[end]):
            end += 1
        return end
    end = start + 2
    while end < len(lines) and _body_row(lines[end]):
        end += 1
    return end


def _body_row(line: str) -> bool:
    if PIPE not in line or line.lstrip().startswith("<!--"):
        return False
    return bool(_boundaries(line))
