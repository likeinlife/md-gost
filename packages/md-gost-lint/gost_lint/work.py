"""A work: one book.toml manifest plus the chapters it lists.

Labels, citations and section numbering are shared across chapters, so
cross-file rules need this grouping; a lone .md is linted as a work of one.
"""

import tomllib
from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Self

from gost_lint.diagram import is_diagram
from gost_lint.markdown import Block, Document

MANIFEST = "book.toml"
PRUNE = (".git", ".venv", ".md-to-gost", "node_modules", "__pycache__")
DefinitionMap = dict[str, Block]
DocumentDefinitions = tuple[Document, DefinitionMap]
DocumentLoader = Callable[[Path, Path], Document | None]


def load_chapter(path: Path, root: Path) -> Document | None:
    """Load chapter."""
    return Document.load(path, root) if path.is_file() else None


@dataclass
class Work:
    """Represent Work."""

    root: Path
    manifest: Path | None
    chapters: list[str]
    docs: list[Document]
    toc: bool = True
    diagrams: list[Path] = field(default_factory=list)
    _focus: set[str] = field(default_factory=set)

    @property
    def focus(self) -> set[str]:
        """Chapter paths that should receive direct diagnostics."""
        return self._focus

    @classmethod
    def from_manifest(
        cls,
        manifest: Path,
        repo_root: Path,
        only: set[str] | None = None,
        *,
        loader: DocumentLoader = load_chapter,
    ) -> Self:
        """Build from manifest."""
        cfg = tomllib.loads(manifest.read_text(encoding="utf-8"))
        chapters = _manifest_chapters(cfg)
        loaded = (loader(manifest.parent / name, repo_root) for name in chapters)
        docs = list(filter(None, loaded))
        return cls(
            manifest.parent,
            manifest,
            chapters,
            docs,
            bool(cfg.get("toc", True)),
            _focus={doc.rel for doc in docs} if only is None else only,
        )

    @classmethod
    def from_file(cls, path: Path, repo_root: Path) -> Self:
        """Lint a single file — with its work's context when there is one."""
        for directory in (path.parent, *path.parent.parents):
            manifest = directory / MANIFEST
            if manifest.exists():
                target = Document.load(path, repo_root)
                work = cls.from_manifest(manifest, repo_root, only={target.rel})
                if target.rel not in {document.rel for document in work.docs}:
                    work.docs.append(target)
                return work
            if directory == repo_root:
                break
        doc = Document.load(path, repo_root)
        return cls(
            path.parent,
            None,
            [path.name],
            [doc],
            _focus={doc.rel},
        )

    @classmethod
    def from_diagram(cls, path: Path, repo_root: Path) -> Self:
        """Build a work from a diagram file and its include chain."""
        root = path.parent
        for directory in (path.parent, *path.parent.parents):
            if (directory / MANIFEST).exists():
                root = directory
                break
            if directory == repo_root:
                break
        return cls(root, None, [], [], diagrams=[path])

    def diagram_sources(self) -> list[Path]:
        """Diagram files to follow: named as targets, or linked from a chapter."""
        found: list[Path] = [path for path in self.diagrams if path.exists()]
        for doc in self.docs:
            for block in doc.of_kind("image"):
                src = block.meta.get("src", "")
                if src and is_diagram(src) and (self.root / src).exists():
                    found.append(self.root / src)
        return found

    def is_lab(self) -> bool:
        """One chapter, no table of contents — the shape every lab here has."""
        return len(self.chapters) == 1 and not self.toc

    def definitions(self) -> list[DocumentDefinitions]:
        """Handle definitions."""
        return [(doc, dict(doc.definitions())) for doc in self.docs]


def find_manifests(directory: Path) -> list[Path]:
    """Find manifests."""
    found: list[Path] = []
    for path in sorted(directory.rglob(MANIFEST)):
        if any(part in PRUNE for part in path.parts):
            continue
        found.append(path)
    return found


def _manifest_chapters(config: dict[str, Any]) -> list[str]:
    chapters = config.get("chapters")
    if not isinstance(chapters, list) or not chapters:
        message = "chapters в book.toml должен содержать непустой список путей к главам"
        raise ValueError(message)
    if not all(isinstance(chapter, str) and chapter for chapter in chapters):
        message = "каждый путь в chapters должен быть непустой строкой"
        raise ValueError(message)
    return chapters
