"""A mechanical source edit and its original location in a Markdown document."""

from collections.abc import Iterable
from dataclasses import dataclass


@dataclass(frozen=True)
class Repair:
    """Represent Repair."""

    rule: str
    line: int
    start: int
    end: int
    text: str
    message: str

    def finding(self) -> tuple[int, int, str]:
        """Handle finding."""
        return self.line + 1, self.start + 1, self.message

    def sort_key(self) -> tuple[int, int, int]:
        """Handle sort key."""
        return self.line, self.start, -self.end

    def follows(self, other: "Repair") -> bool:
        """Handle follows."""
        return self.line != other.line or self.start >= other.end

    def replace(self, source: str) -> str:
        """Handle replace."""
        before = source[: self.start]
        return before + self.text + source[self.end :]


def applicable_repairs(candidates: Iterable[Repair]) -> list[Repair]:
    """Keep repairs that do not overlap an earlier edit."""
    ordered = sorted(candidates, key=Repair.sort_key)
    picked: list[Repair] = []
    for edit in ordered:
        if not picked or edit.follows(picked[-1]):
            picked.append(edit)
    return picked
