"""Fence and listing block parsing."""

import re

from gost_lint.markdown.metadata import QUOTED_ATTRIBUTE, attributes
from gost_lint.markdown.syntax import CAPTION_KEY, FENCE, LABEL_KEY, SOURCE_KEY
from gost_lint.markdown.types import Block

FIGURE_CLASSES = frozenset((".plantuml", ".plot", ".idef0"))


def fence_block(lines: list[str], start: int) -> tuple[Block, int]:
    """Handle fence block."""
    match = FENCE.match(lines[start])
    if match is None:
        message = "fence line does not match"
        raise ValueError(message)
    marker = match.group("fence")
    end = fence_end(lines, start, marker)
    return make_fence_block(lines, start, end, match), end + 1


def make_fence_block(lines: list[str], start: int, end: int, match: re.Match[str]) -> Block:
    """Make fence block."""
    fence_info = match.group("info")
    metadata = attributes(fence_info)
    metadata["body"] = lines[start + 1 : end]
    return Block(
        fence_kind(fence_info, metadata),
        start + 1,
        display_fence_end(end, len(lines)),
        lines[start : end + 1],
        metadata,
    )


def display_fence_end(end: int, line_count: int) -> int:
    """Handle display fence end."""
    return min(end, line_count - 1) + 1


def fence_end(lines: list[str], start: int, marker: str) -> int:
    """Handle fence end."""
    for end, candidate in enumerate(lines):
        if end > start and closes_fence(candidate, marker):
            return end
    return len(lines)


def closes_fence(line: str, marker: str) -> bool:
    """Handle closes fence."""
    if line.startswith("    "):
        return False
    stripped = line.lstrip(" ").rstrip()
    long_enough = len(stripped) >= len(marker)
    return long_enough and set(stripped) == {marker[0]}


def fence_kind(fence_info: str, metadata: dict[str, object]) -> str:
    """Handle fence kind."""
    language = fence_info.strip()
    classes = QUOTED_ATTRIBUTE.sub("", language).strip("{}").split()
    if f".{language}" in FIGURE_CLASSES or FIGURE_CLASSES.intersection(classes):
        return "diagram"
    if metadata.keys() & {LABEL_KEY, CAPTION_KEY, SOURCE_KEY}:
        return "listing"
    return "code"
