"""Typography. Everything here is mechanical, so most of it also auto-fixes."""

import re
from collections.abc import Iterator

from gost_lint.markdown import Document
from gost_lint.markdown.refs import strip_code
from gost_lint.rules.registry import rule
from gost_lint.spacing import EXTRA_SPACE, spaces

FileIssue = Iterator[tuple[int, int, str]]

HYPHEN_DASH = re.compile(r"(?<=[\w»)]) - (?=[\w«(])")
STRAIGHT_QUOTE = re.compile(r'"')
DASH_AS_BULLET = re.compile(r"^\s{0,3}[—–](?=\s)")
CYRILLIC = re.compile(r"[а-яёА-ЯЁ]")
LATIN = re.compile(r"[a-zA-Z]")
WORD = re.compile(r"[\wа-яёА-ЯЁ]+")
SKIP_KINDS = ("code", "diagram", "listing", "comment", "bib_marker", "formula")


def _lines(doc: Document) -> Iterator[tuple[int, str]]:
    for block in doc.blocks:
        if block.kind in SKIP_KINDS:
            continue
        for offset, line in enumerate(block.lines):
            yield block.start + offset, strip_code(line)


@rule("TYPO001", "warning", "дефис вместо тире")
def hyphen_as_dash(doc: Document) -> FileIssue:
    """Handle hyphen as dash."""
    for line, text in _lines(doc):
        for found in HYPHEN_DASH.finditer(text):
            yield (
                line,
                found.start() + 1,
                "дефис между словами — нужно тире «—» (сборка сама заменит его на короткое)",
            )


@rule("TYPO002", "warning", "прямые кавычки вместо «ёлочек»")
def straight_quotes(doc: Document) -> FileIssue:
    """Handle straight quotes."""
    for line, text in _lines(doc):
        found = STRAIGHT_QUOTE.search(text)
        if found:
            yield (line, found.start() + 1, 'прямые кавычки " — в русском тексте ставятся «ёлочки»')


@rule("TYPO003", "warning", "лишние пробелы")
def stray_spaces(doc: Document) -> FileIssue:
    """Handle stray spaces."""
    for repair in spaces(doc, doc.format_scope):
        if repair.rule == EXTRA_SPACE:
            yield repair.finding()


@rule("TYPO004", "error", "латиница внутри русского слова")
def homoglyphs(doc: Document) -> FileIssue:
    """Handle homoglyphs."""
    for line, text in _lines(doc):
        for found in WORD.finditer(text):
            word = found.group(0)
            if CYRILLIC.search(word) and LATIN.search(word):
                yield (
                    line,
                    found.start() + 1,
                    f"«{word}» смешивает кириллицу и латиницу — вероятно, подменены похожие буквы",
                )


@rule("TYPO006", "error", "строка начинается с тире")
def dash_at_line_start(doc: Document) -> FileIssue:
    """Тире в начале строки — почти всегда список, набранный не тем знаком.

    Pandoc маркером его не считает: пункты склеиваются в один абзац и теряют
    отступы. Маркер списка — дефис, на тире его заменит сама сборка.
    """
    for block in doc.of_kind("paragraph"):
        for offset, line in enumerate(block.lines):
            found = DASH_AS_BULLET.match(line)
            if found:
                yield (
                    block.start + offset,
                    found.start() + 1,
                    (
                        "строка начинается с тире — маркер списка набирается дефисом «-», "
                        "иначе пункты соберутся в сплошной абзац"
                    ),
                )
