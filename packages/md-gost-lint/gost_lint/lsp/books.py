"""Read manifest chapters using the current editor buffers over the saved files."""

from collections.abc import Iterator
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

from gost_lint.config import Chain
from gost_lint.markdown import Document
from gost_lint.paths import repository_root
from gost_lint.report import Issue
from gost_lint.rules.registry import load_all as load_rules
from gost_lint.runner import RuleRun, RuleRunner
from gost_lint.work import MANIFEST, Work


@dataclass(frozen=True)
class Buffer:
    """Represent Buffer."""

    uri: str
    version: int | None
    document: Document


def find_manifest(path: Path) -> Path | None:
    """Find manifest."""
    return next(
        (folder / MANIFEST for folder in path.parents if (folder / MANIFEST).is_file()),
        None,
    )


def config_root(manifest: Path, folders: tuple[Path, ...]) -> Path:
    """Handle config root."""
    root = repository_root(manifest.parent)
    if root is not None:
        return root
    return next((ancestor for ancestor in manifest.parents if ancestor in folders), manifest.parent)


@lru_cache
def _disk_document(path: Path, root: Path, _revision: tuple[int, ...]) -> Document:
    """Invalidate the cache when an unopened chapter changes on disk."""
    with path.open(encoding="utf-8", newline="") as stream:
        return Document.from_text(path, root, stream.read())


@dataclass
class Book:
    """Represent Book."""

    root: Path
    work: Work

    def lint(self) -> list[Issue]:
        """Handle lint."""
        config = Chain(self.root)
        registered = load_rules()
        rules = RuleRun(
            works=[self.work],
            rules=registered,
            config=config,
            root=self.root,
            selected=set(),
            ignored=set(),
        )
        return RuleRunner(rules).run()


class Books:
    """A request sees one immutable set of open documents, shared across its books."""

    def __init__(self, buffers: dict[Path, Buffer], folders: tuple[Path, ...]) -> None:
        """Initialize the instance."""
        self.buffers = buffers
        self.folders = folders

    def load(self, manifest: Path) -> Book:
        """Handle load."""
        root = config_root(manifest, self.folders)
        return Book(root, Work.from_manifest(manifest, root, loader=self._chapter))

    def for_document(self, document: Document) -> Book | None:
        """Handle for document."""
        manifest = find_manifest(document.path)
        if manifest is not None:
            book = self.load(manifest)
            if document.rel in book.work.focus:
                return book
        return None

    def active_manifests(self) -> Iterator[Path]:
        """Handle active manifests."""
        known = {find_manifest(path) for path in self.buffers}
        yield from (manifest for manifest in known if manifest is not None)

    def _chapter(self, path: Path, root: Path) -> Document | None:
        path = path.resolve()
        opened = self.buffers.get(path)
        if opened is not None:
            return opened.document
        try:
            metadata = path.stat()
        except FileNotFoundError:
            return None
        revision = (metadata.st_ino, metadata.st_ctime_ns, metadata.st_mtime_ns, metadata.st_size)
        return _disk_document(path, root, revision)
