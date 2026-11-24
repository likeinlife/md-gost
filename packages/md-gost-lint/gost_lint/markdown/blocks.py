"""Builders for single-line, formula, and table blocks."""

import re

from gost_lint.markdown.metadata import attributes, table_rows
from gost_lint.markdown.pipe_rows import table_end
from gost_lint.markdown.syntax import (
    CAPTION_KEY,
    IMAGE,
    LABEL_KEY,
    MATH_DELIM,
)
from gost_lint.markdown.types import Block


def heading_block(line: str, number: int) -> Block:
    """Handle heading block."""
    match = re.match(r"^(?P<hashes>#{1,6})\s+(?P<text>.*?)\s*$", line)
    if match is None:
        message = "heading line does not match"
        raise ValueError(message)
    return Block(
        "heading",
        number,
        number,
        [line],
        {"level": len(match.group("hashes")), "title": match.group("text")},
    )


def marker_block(line: str, number: int, kind: str, match: re.Match[str]) -> Block:
    """Handle marker block."""
    if kind == "table_marker":
        metadata = {
            LABEL_KEY: f"tbl:{match.group('label')}",
            CAPTION_KEY: match.group("caption"),
        }
    elif kind == "eq_marker":
        label = f"eq:{match.group('label')}"
        metadata = {LABEL_KEY: label, "extra": match.group("extra")}
    else:
        metadata = {"key": match.group("key"), "text": match.group("text")}
    return Block(kind, number, number, [line], metadata)


def image_block(line: str, number: int) -> Block:
    """Handle image block."""
    match = IMAGE.match(line)
    if match is None:
        message = "image line does not match"
        raise ValueError(message)
    metadata = attributes(match.group("attrs") or "")
    metadata[CAPTION_KEY] = metadata.get(CAPTION_KEY) or match.group("alt")
    metadata["src"] = match.group("src")
    return Block("image", number, number, [line], metadata)


def formula_block(lines: list[str], start: int) -> tuple[Block, int]:
    """Handle formula block."""
    body = lines[start].strip()[len(MATH_DELIM) :]
    if body.endswith(MATH_DELIM) and body:
        end = start
    else:
        end = start + 1
        while end < len(lines) and MATH_DELIM not in lines[end]:
            end += 1
        end = min(end, len(lines) - 1)
    block_end = end + 1
    block_lines = lines[start:block_end]
    return Block("formula", start + 1, block_end, block_lines), block_end


def table_block(lines: list[str], start: int) -> tuple[Block, int]:
    """Handle table block."""
    end = table_end(lines, start)
    body = lines[start:end]
    metadata = {"rows": table_rows(body)}
    return Block("table", start + 1, end, body, metadata), end
