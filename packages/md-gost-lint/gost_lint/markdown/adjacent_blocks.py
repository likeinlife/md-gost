"""Typed adjacent block relationships used by block-level rules."""

from collections.abc import Iterator

from gost_lint.markdown.types import Block


def with_next(blocks: list[Block]) -> Iterator[tuple[Block, Block | None]]:
    """Handle with next."""
    for index, block in enumerate(blocks):
        next_index = index + 1
        next_block = blocks[next_index] if next_index < len(blocks) else None
        yield block, next_block


def with_previous(blocks: list[Block]) -> Iterator[tuple[Block | None, Block]]:
    """Handle with previous."""
    previous = None
    for block in blocks:
        yield previous, block
        previous = block
