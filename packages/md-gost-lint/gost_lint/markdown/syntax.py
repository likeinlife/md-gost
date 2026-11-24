"""Patterns and metadata keys used by the Markdown block parser."""

import re

FENCE = re.compile(r"^ {0,3}(?P<fence>`{3,}|~{3,})(?P<info>.*)$")
HEADING = re.compile(r"^(?P<hashes>#{1,6})\s+(?P<text>.*?)\s*$")
APPENDIX_HEADING = re.compile(r"^Приложение\s+[А-ЯЁ]\.\s+\S", re.IGNORECASE)
TBL_MARKER = re.compile(r"^<!--\s*#tbl:(?P<label>[\w-]+)\s*(?P<caption>.*?)\s*-->\s*$")
EQ_MARKER = re.compile(r"^<!--\s*#eq:(?P<label>[\w-]+)\s*(?P<extra>.*?)\s*-->\s*$")
BIB_MARKER = re.compile(r"^<!--\s*#bib:(?P<key>[\w-]+)\s*(?P<text>.*?)\s*-->\s*$")
COMMENT = re.compile(r"^<!--.*-->\s*$")
LIST_ITEM = re.compile(r"^\s{0,3}(?:[-*+]|\d+[.)])\s+\S")
TABLE_ROW = re.compile(r"^\s{0,3}\|")
FORMULA_FENCE = re.compile(r"^\s{0,3}\$\$")
MATH_DELIM = "$$"
IMAGE = re.compile(
    r"^\s*!\[(?P<alt>[^\]]*)\]\((?P<src>[^)]*)\)"
    r"(?:\{(?P<attrs>[^}]*)\})?\s*$",
)
LABEL = re.compile(r"#(?P<kind>fig|tbl|lst):(?P<name>[\w-]+)")
REFERENCE = re.compile(r"\[(?P<body>@[^\]]+)\]")
REF_KEY = re.compile(r"@(?P<kind>fig|tbl|bib|eq|lst):(?P<name>[\w-]+)")
INLINE_CODE = re.compile(r"`[^`]*`")
ATTACHMENT = ("table", "diagram", "image", "formula", "listing")
PROSE = ("paragraph",)
LABEL_KEY = "label"
CAPTION_KEY = "caption"
SOURCE_KEY = "src"


def is_grid_line(line: str) -> bool:
    """Return whether grid line."""
    return line.lstrip().startswith(("+", "|"))


def source_lines(text: str) -> list[str]:
    """Split physical editor lines, preserving Unicode paragraph and line separators as text."""
    normalized = text.replace("\r\n", "\n").replace("\r", "\n")
    if not normalized:
        return []
    return normalized.removesuffix("\n").split("\n")
