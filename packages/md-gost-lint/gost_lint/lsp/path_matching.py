"""Filter path completions by relative path, basename or extension."""

from collections.abc import Iterable
from pathlib import PurePosixPath

SEPARATOR = "/"


def matching_names(names: Iterable[str], prefix: str) -> list[str]:
    """Handle matching names."""
    parent, slash, word = prefix.casefold().rpartition(SEPARATOR)
    directory = parent + slash
    matches = [name for name in names if _matches(name.casefold(), directory, word)]
    return sorted(matches, key=_order)


def _order(name: str) -> tuple[int, str, str]:
    return name.count(SEPARATOR), name.casefold(), name


def _matches(name: str, directory: str, word: str) -> bool:
    if not name.startswith(directory):
        return False
    if name.startswith(directory + word):
        return True
    if name.endswith(SEPARATOR):
        return False
    leaf = PurePosixPath(name)
    if word.startswith("."):
        return leaf.suffix.startswith(word)
    return leaf.name.startswith(word)
