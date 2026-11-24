"""Complete single references and semicolon-separated bibliography groups."""

import re
from dataclasses import dataclass

from gost_lint.lsp.completion_types import Suggestion
from gost_lint.lsp.titles import title_for
from gost_lint.markdown import Document

GROUP = re.compile(r"(?<!\\)\[(?P<previous>(?:@bib:[\w-]+;\s*)*)(?P<at>@?)(?P<prefix>[\w:-]*)$")
KEY_TAIL = re.compile(r"[\w:-]*")
BIB_PREFIX = "bib:"


@dataclass(frozen=True)
class Reference:
    """Represent Reference."""

    prefix: str
    start: int
    end: int
    at: str
    closing: str
    bibliography: bool

    def suggestions(self, documents: list[Document]) -> list[Suggestion]:
        """Handle suggestions."""
        choices: dict[str, Suggestion] = {}
        for document in documents:
            for span, block in document.definition_spans():
                if self.matches(span.label) and span.label not in choices:
                    detail = _description(title_for(document, block), document.rel)
                    choices[span.label] = self._choice(span.label, detail)
        return list(choices.values())

    def matches(self, label: str) -> bool:
        """Handle matches."""
        return label.startswith(self.prefix) and (
            not self.bibliography or label.startswith(BIB_PREFIX)
        )

    def _choice(self, label: str, detail: str) -> Suggestion:
        insertion = f"{self.at}{label}{self.closing}"
        return Suggestion(label, detail, insertion, self.start, self.end)


def reference_at(source: str, column: int) -> Reference | None:
    """Handle reference at."""
    match = GROUP.search(source[:column])
    if match is None or not (match["at"] or match["previous"]):
        return None
    tail = KEY_TAIL.match(source, column)
    if tail is None:
        message = "reference has no tail"
        raise ValueError(message)
    following = source[tail.end() :].lstrip()
    return Reference(
        match["prefix"],
        match.start("prefix"),
        tail.end(),
        "" if match["at"] else "@",
        "" if following.startswith(("]", ";")) else "]",
        bool(match["previous"]) or following.startswith(";"),
    )


def _description(title: str, chapter: str) -> str:
    return f"{chapter} — {title}" if title else chapter
