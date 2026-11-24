"""Complete relative Markdown destinations using book assets and chapter paths."""

import os
import re
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import quote, unquote

from gost_lint.lsp.completion_files import file_names
from gost_lint.lsp.completion_types import Suggestion
from gost_lint.lsp.path_matching import matching_names
from gost_lint.markdown import Document

OPENER = r"(?<![!\\])(?P<image>!)?\[(?:\\.|[^\[\]\\]|\[[^\[\]]*\])*\]\("
PATH_TEXT = r"[^()<>#:?\"'\\]*"
DESTINATION = re.compile(rf"{OPENER}(?P<path>{PATH_TEXT})$")
TAIL = re.compile(rf"{PATH_TEXT}?(?=\s+[\"']|[)#?]|$)")
URL_ESCAPE = re.compile(r"[^\w./~-]")


@dataclass(frozen=True)
class Destination:
    """Represent Destination."""

    prefix: str
    image: bool
    start: int
    end: int
    closing: str

    def suggest(self, name: str) -> Suggestion:
        """Handle suggest."""
        path = name if self.image else URL_ESCAPE.sub(_escape, name)
        ending = "" if name.endswith("/") else self.closing
        detail = "Путь к рисунку" if self.image else "Путь в работе"
        return Suggestion(name, detail, path + ending, self.start, self.end, filter_text=name)


def _escape(match: re.Match[str]) -> str:
    return quote(match[0], safe="")


def _destination(source: str, column: int) -> Destination | None:
    match = DESTINATION.search(source[:column])
    if match is None:
        return None
    tail = TAIL.match(source, column)
    if tail is None:
        return None
    closing = _closing(source[tail.end() :])
    prefix = unquote(match["path"])
    bounds = match.start("path"), tail.end()
    return Destination(prefix, bool(match["image"]), *bounds, closing)


def _closing(suffix: str) -> str:
    delimiters = (")", "#", "?", '"', "'")
    return "" if suffix.lstrip().startswith(delimiters) else ")"


def path_suggestions(
    document: Document,
    documents: list[Document],
    work_root: Path,
    line: int,
    column: int,
) -> list[Suggestion]:
    """Handle path suggestions."""
    if line >= len(document.lines) or not document.is_prose_position(line, column):
        return []
    destination = _destination(document.lines[line], column)
    if destination is None:
        return []
    base = work_root if destination.image else document.path.parent
    names = set(file_names(destination.prefix, base, work_root, image=destination.image))
    if not destination.image:
        names.update(os.path.relpath(chapter.path, base) for chapter in documents)
    return [destination.suggest(name) for name in matching_names(names, destination.prefix)]
