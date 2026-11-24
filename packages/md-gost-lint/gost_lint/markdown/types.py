"""Common block and section types for the Markdown document model."""

from dataclasses import dataclass, field
from typing import Any

from gost_lint.markdown.syntax import APPENDIX_HEADING


@dataclass
class Block:
    """Represent Block."""

    kind: str
    start: int
    end: int
    lines: list[str]
    meta: dict[str, Any] = field(default_factory=dict)

    @property
    def text(self) -> str:
        """Handle text."""
        return "\n".join(self.lines)

    @property
    def level(self) -> int:
        """Handle level."""
        return self.meta.get("level", 0)

    @property
    def is_appendix(self) -> bool:
        """Return whether appendix."""
        title = self.meta.get("title", "")
        return self.level == 1 and APPENDIX_HEADING.match(title) is not None


Section = tuple[Block, list[Block]]
