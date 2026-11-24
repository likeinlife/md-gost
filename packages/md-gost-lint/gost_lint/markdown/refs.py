"""Source ranges of declarations and Pandoc reference keys."""

import re
from collections.abc import Iterator
from dataclasses import dataclass

from gost_lint.markdown.metadata import attribute_label
from gost_lint.markdown.syntax import IMAGE, INLINE_CODE, REF_KEY, REFERENCE
from gost_lint.markdown.types import Block

MARKERS = frozenset(("table_marker", "eq_marker", "bib_marker"))
LABELED_BLOCKS = frozenset(("diagram", "image", "listing"))


@dataclass(frozen=True)
class LabelSpan:
    """A key without its sigil, in zero-based Python code points, end exclusive."""

    label: str
    line: int
    start: int
    end: int

    def lint_location(self) -> tuple[str, int, int]:
        """Handle lint location."""
        return self.label, self.line + 1, self.start + 1


def declaration(block: Block) -> LabelSpan | None:
    """Handle declaration."""
    line = block.lines[0]
    if block.kind in MARKERS:
        label = _marker_label(block)
        start = line.index(f"#{label}") + 1
    elif block.kind in LABELED_BLOCKS and "label" in block.meta:
        label = block.meta["label"]
        start = _attribute_start(line, block.kind)
    else:
        return None
    return LabelSpan(label, block.start - 1, start, start + len(label))


def _marker_label(block: Block) -> str:
    if block.kind == "bib_marker":
        return f"bib:{block.meta['key']}"
    return block.meta["label"]


def _attribute_start(line: str, kind: str) -> int:
    image = IMAGE.match(line) if kind == "image" else None
    offset = image.start("attrs") if image else 0
    match = attribute_label(line[offset:])
    if match is None:
        message = "attribute label does not match"
        raise ValueError(message)
    return offset + match.start("kind")


def line_key_spans(line: str, number: int) -> Iterator[LabelSpan]:
    """Handle line key spans."""
    for reference in REFERENCE.finditer(line):
        for key in REF_KEY.finditer(reference["body"]):
            start = reference.start("body") + key.start("kind")
            label = f"{key['kind']}:{key['name']}"
            yield LabelSpan(label, number, start, start + len(label))


def _mask_inline_code(match: re.Match[str]) -> str:
    return " " * len(match.group(0))


def strip_code(text: str) -> str:
    """Blank out inline code so style rules do not fire on `ruff`-like spans."""
    return INLINE_CODE.sub(_mask_inline_code, text)
