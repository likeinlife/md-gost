"""Address each repair in the current Markdown snapshot, in Python code points."""

import re
from collections.abc import Iterator

from gost_lint.markdown import Document
from gost_lint.markdown.format_scope import FormatScope
from gost_lint.repairs import Repair

EXTRA_SPACE = "TYPO003"
WHITESPACE = "TYPO005"
WHITESPACE_RULES = (EXTRA_SPACE, WHITESPACE)
GAP = re.compile(r"[ \t]+")
PUNCTUATION = re.compile(r"[,;:!?](?=\s|$)")
# Padding after Pandoc list markers changes list nesting and can introduce code.
ORDINAL = r"(?:[0-9]+|[a-zA-Z]|[ivxlcdmIVXLCDM]+|#|@[\w-]*)"
MARKER = rf"(?:[-+*:~]|#{{1,6}}|>+|\(?{ORDINAL}[.)]|\[[ xX]\])"
MARKED_PREFIX = re.compile(rf"^[ \t]*(?:{MARKER}[ \t]+)+")
CODE_PADDING = re.compile(r" {4}|\t")
TAB_WIDTH = 4
HARD_BREAK = "  "
Change = tuple[str, str, str]


def _inner_gap(line: str, match: re.Match[str]) -> Change | None:
    start, end = match.span()
    if not start:
        return None
    if PUNCTUATION.match(line, end) and _join_punctuation(line, start, end):
        return EXTRA_SPACE, "", "пробел перед знаком препинания"
    if "\t" in match[0]:
        return WHITESPACE, " ", "табуляция в тексте"
    if len(match[0]) > 1:
        return EXTRA_SPACE, " ", "два пробела подряд"
    return None


def _join_punctuation(line: str, start: int, end: int) -> bool:
    # Joining a delimiter to punctuation can turn prose into emphasis or a reference definition.
    previous = line[start - 1]
    caption = line[:start].strip().casefold() == "table"
    if line[end] == ":" and caption:
        return False
    return previous.isalnum() or previous in "»”)"


def _spacing(doc: Document, number: int, match: re.Match[str]) -> Repair | None:
    line = doc.lines[number]
    if match.end() == len(line):
        return _trailing(doc, number, match)
    change = _inner_gap(line, match)
    if change is None:
        return None
    rule, text, message = change
    return Repair(rule, number, *match.span(), text, message)


def _trailing(doc: Document, number: int, match: re.Match[str]) -> Repair | None:
    following = doc.lines[number + 1 : number + 2]
    continues = bool(match.start() and following and following[0].strip())
    keep_break = continues and _break_width(match) >= len(HARD_BREAK)
    text = HARD_BREAK if keep_break else ""
    if text == match[0]:
        return None
    return Repair(WHITESPACE, number, *match.span(), text, "пробелы в конце строки")


def _break_width(match: re.Match[str]) -> int:
    if "\t" in match[0]:
        line = match.string
        before = line[: match.start()].expandtabs(TAB_WIDTH)
        return len(line.expandtabs(TAB_WIDTH)) - len(before)
    return len(match[0])


def _gaps(line: str) -> Iterator[re.Match[str]]:
    prefix = MARKED_PREFIX.match(line)
    if prefix and CODE_PADDING.search(prefix[0]):
        return
    yield from GAP.finditer(line, prefix.end() if prefix else 0)


def spaces(doc: Document, scope: FormatScope) -> Iterator[Repair]:
    """Handle spaces."""
    for number, line in enumerate(doc.lines):
        for match in _gaps(line):
            repair = _spacing(doc, number, match)
            if repair and scope.editable(number, repair.start, repair.end):
                yield repair
