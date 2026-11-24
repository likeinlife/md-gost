"""Cache a book's directory entries and read only as deep as the quick search needs."""

import os
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

from gost_lint.work import PRUNE

SEARCH_DEPTH = 2
REVISION_CACHE_SIZE = 1024
Paths = tuple[Path, ...]


def _hidden(part: str) -> bool:
    return part.startswith(".") or part in PRUNE


def visible(path: Path, root: Path) -> bool:
    """Handle visible."""
    try:
        relative = path.resolve().relative_to(root)
    except (OSError, RuntimeError, ValueError):
        return False
    return not any(_hidden(part) for part in relative.parts)


@dataclass(frozen=True)
class Directory:
    """Represent Directory."""

    files: Paths = ()
    folders: Paths = ()
    symlinks: Paths = ()

    @classmethod
    def read(cls, folder: Path) -> "Directory":
        """Handle read."""
        with os.scandir(folder) as stream:
            entries = [entry for entry in stream if not _hidden(entry.name)]
        return cls(
            tuple(Path(entry.path) for entry in entries if entry.is_file(follow_symlinks=False)),
            tuple(Path(entry.path) for entry in entries if entry.is_dir(follow_symlinks=False)),
            tuple(Path(entry.path) for entry in entries if entry.is_symlink()),
        )

    def browse(self, root: Path) -> tuple[Paths, Paths]:
        """Resolve symlinks at request time, even if their own parent did not change."""
        links = [path for path in self.symlinks if visible(path, root)]
        files = tuple(path for path in links if path.is_file())
        folders = tuple(path for path in links if path.is_dir())
        return self.files + files, self.folders + folders


@lru_cache(maxsize=REVISION_CACHE_SIZE)
def _read(folder: Path, _revision: tuple[int, int, int]) -> Directory:
    return Directory.read(folder)


def _revision(folder: Path) -> tuple[int, int, int]:
    stat = folder.stat()
    return stat.st_ino, stat.st_mtime_ns, stat.st_ctime_ns


def directory(folder: Path, root: Path) -> Directory:
    """Handle directory."""
    if not visible(folder, root):
        return Directory()
    try:
        return _read(folder, _revision(folder))
    except (OSError, ValueError):
        return Directory()


def shallow_directories(root: Path) -> list[Directory]:
    """Handle shallow directories."""
    folders = [root]
    found: list[Directory] = []
    for _ in range(SEARCH_DEPTH + 1):
        level = [directory(folder, root) for folder in folders]
        found.extend(level)
        folders = [child for listing in level for child in listing.folders]
    return found
