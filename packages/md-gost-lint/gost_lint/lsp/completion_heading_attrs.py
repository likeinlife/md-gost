"""Completions for Pandoc attributes on a heading line."""

import re
from collections.abc import Iterator
from dataclasses import dataclass

from gost_lint.lsp.completion_types import Suggestion
from gost_lint.markdown import Document

_TOKEN = re.compile(r"[^\s{}]+")
_KINDS = (
    ("-", "unnumbered"),
    (".unnumbered", "unnumbered"),
    (".page", "page"),
    (".landscape", "landscape"),
)
_PROPERTIES = (
    ("-", "без номера", ("-",)),
    (".unnumbered", "без номера, полная форма", (".unnumbered", "unnumbered")),
    (".page", "с новой страницы", (".page", "page")),
    (".landscape", "альбомная ориентация", (".landscape", "landscape")),
    ("paper=a3", "формат А3", ("paper=a3", "paper")),
)


@dataclass(frozen=True)
class _Edit:
    """Represent Edit."""

    prefix: str
    start: int
    end: int
    suffix: str
    used: frozenset[str]

    def choices(self) -> Iterator[Suggestion]:
        """Handle choices."""
        folded = self.prefix.casefold()
        for label, detail, names in _PROPERTIES:
            matched = _name(names, folded)
            if matched is None:
                continue
            if _kind(label) in self.used:
                continue
            yield self._suggestion(label, detail, matched)

    def _suggestion(self, label: str, detail: str, matched: str) -> Suggestion:
        return Suggestion(
            label,
            detail,
            f"{label}{self.suffix}",
            self.start,
            self.end,
            filter_text=matched,
        )


class _Scan:
    """Scan one heading line for an open attribute list."""

    def __init__(self, line: str, column: int) -> None:
        """Initialize the instance."""
        self.line = line
        self.column = column

    def edit(self) -> _Edit | None:
        """Handle edit."""
        opener = self._opener()
        if opener is None:
            return None
        start = self._token_start(opener)
        end = self._token_end(start)
        return _Edit(
            self.line[start : self.column],
            start,
            end,
            self._suffix(end),
            self._used(opener, start, end),
        )

    def _opener(self) -> int | None:
        opener = self.line.rfind("{", 0, self.column)
        if opener < 0:
            return None
        if self.line.find("}", opener, self.column) >= 0:
            return None
        return opener

    def _token_start(self, opener: int) -> int:
        space = self.line.rfind(" ", opener, self.column)
        tab = self.line.rfind("\t", opener, self.column)
        return max(space, tab, opener) + 1

    def _token_end(self, start: int) -> int:
        if start == self.column:
            return self.column
        found = _TOKEN.match(self.line, self.column)
        if found is None:
            return self.column
        return found.end()

    def _suffix(self, end: int) -> str:
        rest = self.line[end:]
        if not rest.strip():
            return "}"
        if rest[0] in " \t}":
            return ""
        return " "

    def _used(self, opener: int, start: int, end: int) -> frozenset[str]:
        tokens = _TOKEN.findall(_body(self.line, opener, start, end))
        return frozenset(filter(None, (_kind(token) for token in tokens)))


def heading_attribute_suggestions(
    document: Document,
    line: int,
    column: int,
) -> list[Suggestion] | None:
    """Handle heading attribute suggestions."""
    if not _heading(document, line):
        return None
    if line >= len(document.lines):
        return None
    edit = _Scan(document.lines[line], column).edit()
    if edit is None:
        return None
    return list(edit.choices())


def _name(names: tuple[str, ...], folded: str) -> str | None:
    return next((name for name in names if name.casefold().startswith(folded)), None)


def _kind(label: str) -> str:
    for name, kind in _KINDS:
        if name == label:
            return kind
    if label.startswith("paper="):
        return "paper"
    return ""


def _body(line: str, opener: int, start: int, end: int) -> str:
    close = line.find("}", opener)
    stop = len(line) if close < 0 else close
    head = line[opener + 1 : start]
    return head + line[end:stop]


def _heading(document: Document, line: int) -> bool:
    for block in document.blocks:
        same_line = block.start == line + 1
        if block.kind == "heading" and same_line:
            return True
    return False
