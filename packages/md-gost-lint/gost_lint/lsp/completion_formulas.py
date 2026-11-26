"""Offer the symbols of a display formula while its explanation is typed."""

import re

from gost_lint.lsp.completion_types import Suggestion
from gost_lint.markdown import Block, Document

WHERE = re.compile(r"^\s*[Гг]де\s")
SLOT = re.compile(r"^(?:где\s+)?\$(?P<partial>[^$]*)$", re.IGNORECASE)
USED = re.compile(r"\$([^$]+)\$")
ATOM = re.compile(
    r"\\(?P<command>[A-Za-z]+)"
    r"|(?P<name>[A-Za-zА-Яа-яЁё]+)"
    r"(?:_\{(?P<braced>[A-Za-zА-Яа-яЁё0-9, ]+)\}|_(?P<plain>[A-Za-zА-Яа-яЁё0-9]+))?",
)
# Commands that structure a formula. The symbols inside their braces stay visible.
LAYOUT = (
    "frac",
    "dfrac",
    "tfrac",
    "cfrac",
    "left",
    "right",
    "big",
    "Big",
    "bigl",
    "bigr",
    "biggl",
    "biggr",
    "mathrm",
    "mathbf",
    "text",
    "textit",
    "operatorname",
    "displaystyle",
    "limits",
    "nolimits",
    "sum",
    "prod",
    "int",
    "oint",
    "lim",
    "binom",
    "over",
    "cdot",
    "times",
    "quad",
    "qquad",
    "ldots",
    "cdots",
    "dots",
)
Found = tuple[Block, str]
Slot = tuple[int, str]


def formula_symbol_suggestions(
    document: Document,
    line: int,
    column: int,
) -> list[Suggestion] | None:
    """Complete `$symbol$ — ` from the formula above a «где» paragraph."""
    found = _explication(document, line)
    if found is None:
        return None
    slot = _slot(document.lines[line][:column])
    if slot is None:
        return None
    return _choices(found, slot, column)


def _choices(found: Found, slot: Slot, column: int) -> list[Suggestion]:
    paragraph, latex = found
    start, partial = slot
    explained = _used("\n".join(paragraph.lines))
    return [
        Suggestion(symbol, "из формулы", f"${symbol}$ — ", start, column)
        for symbol in _symbols(latex)
        if symbol.startswith(partial) and symbol not in explained
    ]


def _explication(document: Document, line: int) -> Found | None:
    paragraph = next(
        (
            block
            for block in document.blocks
            if block.kind == "paragraph" and block.start <= line + 1 <= block.end
        ),
        None,
    )
    if paragraph is None or WHERE.match(paragraph.lines[0]) is None:
        return None
    earlier = [block for block in document.blocks if block.end < paragraph.start]
    if not earlier or earlier[-1].kind != "formula":
        return None
    text = "\n".join(earlier[-1].lines).strip()
    latex = text.removeprefix("$$").removesuffix("$$").strip()
    return paragraph, latex


def _slot(before: str) -> Slot | None:
    match = SLOT.match(before)
    if match is None:
        return None
    return match.start("partial") - 1, match["partial"]


def _symbols(latex: str) -> list[str]:
    found: list[str] = []
    seen: set[str] = set()
    for match in ATOM.finditer(latex):
        token = _token(match)
        if token and token not in seen:
            seen.add(token)
            found.append(token)
    return found


def _token(match: re.Match[str]) -> str:
    command = match.group("command")
    if command is not None:
        return "" if command in LAYOUT else rf"\{command}"
    name = match.group("name")
    braced = match.group("braced")
    if braced is not None:
        return f"{name}_{{{braced}}}"
    plain = match.group("plain")
    if plain is not None:
        return f"{name}_{plain}"
    return name


def _used(text: str) -> set[str]:
    return set(USED.findall(text))
