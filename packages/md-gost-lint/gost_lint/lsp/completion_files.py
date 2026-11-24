"""Browse a typed directory or suggest matching resources from a book's shallow index."""

import os
import re
from collections.abc import Iterator
from dataclasses import dataclass
from pathlib import Path

from gost_lint.diagram import SUFFIXES
from gost_lint.lsp.asset_catalog import directory, shallow_directories

RASTER_AND_SVG = frozenset((".png", ".jpg", ".jpeg", ".svg"))
DIAGRAM_FILES = frozenset((*SUFFIXES, ".py", ".idef0"))
IMAGE_SYNTAX = re.compile(r"[()<>#?%:\"'\\\r\n\t]")
LOCAL_SEPARATOR = "/"
Suffixes = frozenset[str] | None


def warm_file_catalog(root: Path) -> None:
    """Handle warm file catalog."""
    shallow_directories(root)


@dataclass(frozen=True)
class FileSelection:
    """Represent File Selection."""

    root: Path
    image: bool
    suffixes: Suffixes

    def accepts(self, path: Path) -> bool:
        """Handle accepts."""
        suffix = path.suffix.lower()
        if self.suffixes is not None and suffix not in self.suffixes:
            return False
        if not self.image:
            return True
        name = path.relative_to(self.root).as_posix()
        if IMAGE_SYNTAX.search(name):
            return False
        if suffix in DIAGRAM_FILES:
            # Pandoc passes escaped spaces to the diagram renderers as literal %20.
            return " " not in name
        return suffix in RASTER_AND_SVG

    def browse(self, folder: Path, prefix: str) -> Iterator[str]:
        """Handle browse."""
        files, folders = directory(folder, self.root).browse(self.root)
        yield from (f"{prefix}{child.name}/" for child in folders)
        yield from (f"{prefix}{child.name}" for child in files if self.accepts(child))

    def indexed(self, base: Path) -> Iterator[str]:
        """Handle indexed."""
        for listing in shallow_directories(self.root):
            files, _ = listing.browse(self.root)
            for path in files:
                if path.parent != base and self.accepts(path):
                    yield os.path.relpath(path, base)


def file_names(
    prefix: str,
    base: Path,
    root: Path,
    *,
    image: bool,
    suffixes: Suffixes = None,
) -> Iterator[str]:
    """Handle file names."""
    if prefix.startswith((LOCAL_SEPARATOR, "~")):
        return
    selection = FileSelection(root, image, suffixes)
    parent, slash, _ = prefix.rpartition(LOCAL_SEPARATOR)
    yield from selection.browse(base / parent, parent + slash)
    if not slash:
        yield from selection.indexed(base)
