"""Derive Pandoc-style automatic section identifiers from heading text."""

import re
from collections.abc import Iterator
from html import unescape

CODE = re.compile(r"(?<!`)(?P<ticks>`+)(?!`)(?P<body>.*?)(?<!`)(?P=ticks)(?!`)")
INLINE_LINK = re.compile(r"\[([^\]]*)\]\([^)]*\)")
AUTOLINK = re.compile(r"<([^<>\s]+(?:@|:)[^<>\s]+)>")
UNDERSCORES = re.compile(r"(?<!\w)(_+)([^\s_].*?)\1(?!\w)")
IGNORED = re.compile(r"\[\^[^\]]*\]|\^\[[^\]]*\]|<[^<>]+>|-{2,}|\.{3}")
NON_IDENTIFIER = re.compile(r"[^\w.\s-]")
BEFORE_LETTER = re.compile(r"^[\W\d_]*")


def _plain_text(source: str) -> str:
    linked = INLINE_LINK.sub(r"\1", AUTOLINK.sub(r"\1", source))
    return unescape(UNDERSCORES.sub(r"\2", IGNORED.sub("", linked)))


def _heading_text(title: str) -> Iterator[str]:
    start = 0
    for match in CODE.finditer(title):
        preceding = _plain_text(title[start : match.start()])
        yield from (preceding, match["body"])
        start = match.end()
    yield _plain_text(title[start:])


def automatic_id(title: str, used: set[str]) -> str:
    """Handle automatic id."""
    plain = "".join(_heading_text(title))
    words = NON_IDENTIFIER.sub("", plain.lower()).split()
    base = BEFORE_LETTER.sub("", "-".join(words)) or "section"
    return _available(base, used)


def _available(base: str, used: set[str]) -> str:
    key = base
    suffix = 0
    while key in used:
        suffix += 1
        key = f"{base}-{suffix}"
    return key
