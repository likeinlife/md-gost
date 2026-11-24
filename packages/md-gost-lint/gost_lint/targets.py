"""Resolve command-line paths to lintable works."""

from pathlib import Path

from gost_lint.diagram import is_diagram
from gost_lint.work import Work, find_manifests


class Targets:
    """Path validation and work discovery operations."""

    lintable = (".md", ".puml", ".iuml")

    def check_targets(self, paths: list[Path]) -> list[str]:
        """Check targets."""
        problems: list[str] = []
        allowed = ", ".join(self.lintable)
        for target in paths:
            if not target.exists():
                problems.append(f"путь не найден: {target}")
            elif target.is_file() and target.suffix.lower() not in self.lintable:
                problems.append(f"проверять можно только {allowed}: {target}")
        return problems

    def collect_works(self, paths: list[Path], root: Path) -> list[Work]:
        """Collect works."""
        works: list[Work] = []
        seen: set[Path] = set()
        for target in paths:
            works.extend(self._works_for_target(target.resolve(), root, seen))
        return works

    def _works_for_target(self, target: Path, root: Path, seen: set[Path]) -> list[Work]:
        if target.is_file():
            return [self._work_from_file(target, root)]
        manifests = find_manifests(target)
        if not manifests:
            return [Work.from_file(markdown, root) for markdown in sorted(target.rglob("*.md"))]
        return self._works_from_manifests(manifests, root, seen)

    def _work_from_file(self, target: Path, root: Path) -> Work:
        if is_diagram(target):
            return Work.from_diagram(target, root)
        return Work.from_file(target, root)

    def _works_from_manifests(
        self,
        manifests: list[Path],
        root: Path,
        seen: set[Path],
    ) -> list[Work]:
        works: list[Work] = []
        for manifest in manifests:
            if manifest not in seen:
                seen.add(manifest)
                works.append(Work.from_manifest(manifest, root))
        return works
