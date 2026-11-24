"""PlantUML sources referenced from the chapters (.puml / .iuml).

The build includes such a file instead of copying it, so PlantUML resolves a
relative `!include` against the directory of the file that spells it out. The
walk below repeats exactly that rule, otherwise a broken include would only
surface as a failed render.
"""

import re
from collections.abc import Iterator
from dataclasses import dataclass
from pathlib import Path

SUFFIXES = (".puml", ".iuml")
# `!include foo.iuml`, `!includesub foo.puml!part`, `!include_many list.iuml`
INCLUDE = re.compile(r"^\s*!include(?:sub|_many)?\s+(?P<target>\S+)", re.IGNORECASE)
# Not a local file: a URL, a bundled stdlib entry (`<archimate/Archimate>`),
# or a path built from a variable — none of them can be checked on disk.
REMOTE = ("http://", "https://")
DYNAMIC = ("%", "$", "<")


def is_diagram(path: str | Path) -> bool:
    """Return whether diagram."""
    return str(path).lower().endswith(SUFFIXES)


@dataclass
class Include:
    """Represent Include."""

    source: Path  # file holding the directive
    line: int
    target: str  # path as written
    path: Path  # resolved against source.parent


def includes(path: Path) -> Iterator[Include]:
    """Local `!include` directives of one diagram file, in source order."""
    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return
    yield from _local_includes(path, text)


def _local_includes(path: Path, text: str) -> Iterator[Include]:
    for number, line in enumerate(text.splitlines(), 1):
        include = INCLUDE.match(line)
        if include is None:
            continue
        target = include.group("target")
        name = _local_target(target)
        if name is not None:
            yield Include(path, number, target, (path.parent / name).resolve())


def _local_target(target: str) -> str | None:
    if target.startswith(REMOTE) or target.startswith(DYNAMIC):
        return None
    # `file.puml!section` includes one named part of a file.
    name = target.split("!", 1)[0]
    return name or None


def walk(path: Path, seen: set[Path] | None = None) -> Iterator[Include]:
    """Every include reachable from `path`, depth-first, cycles cut."""
    if seen is None:
        seen = set()
    resolved = path.resolve()
    if resolved in seen:
        return
    seen.add(resolved)
    for include in includes(resolved):
        yield include
        if include.path.exists() and is_diagram(include.path):
            yield from walk(include.path, seen)
