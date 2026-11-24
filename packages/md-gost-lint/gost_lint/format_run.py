"""Apply chapter formatting to the files selected on the command line."""

import difflib
import sys
from dataclasses import dataclass
from pathlib import Path

from gost_lint.cli import USAGE_ERROR, CommandContext
from gost_lint.formatter import format_text
from gost_lint.markdown import Document

PREFIX = "md-gost"


@dataclass(frozen=True)
class Change:
    """Represent Change."""

    rel: str
    path: Path
    before: str
    after: str


def _read(path: Path) -> str:
    with path.open(encoding="utf-8", newline="") as stream:
        return stream.read()


def _write_files(changed: list[Change]) -> None:
    for change in changed:
        change.path.write_bytes(change.after.encode("utf-8"))


def _write_diff(changed: list[Change]) -> None:
    for change in changed:
        diff = difflib.unified_diff(
            change.before.splitlines(keepends=True),
            change.after.splitlines(keepends=True),
            fromfile=change.rel,
            tofile=change.rel,
        )
        sys.stdout.writelines(diff)


class Session:
    """Format the Markdown files a lint target would include."""

    def __init__(self, paths: list[Path], *, checking: bool, showing_diff: bool) -> None:
        """Initialize the instance."""
        self.checking = checking
        self.showing_diff = showing_diff
        self.context = CommandContext(paths, use_config=False)

    def run(self) -> int:
        """Handle run."""
        if self._rejected():
            return USAGE_ERROR
        documents = self._targets()
        if documents:
            return self._rewrite(documents)
        listed = ", ".join(str(path) for path in self.context.paths)
        sys.stderr.write(f"{PREFIX}: форматировать нечего — в {listed} нет файлов .md\n")
        return 0

    def _rejected(self) -> bool:
        problems = self.context.targets.check_targets(self.context.paths)
        for problem in problems:
            sys.stderr.write(f"{PREFIX}: {problem}\n")
        return bool(problems)

    def _targets(self) -> list[Document]:
        found: list[Document] = []
        for work in self.context.works:
            found.extend(doc for doc in work.docs if doc.rel in work.focus)
        return found

    def _change(self, document: Document) -> Change | None:
        before = _read(document.path)
        after = format_text(before)
        if after == before:
            return None
        return Change(document.rel, document.path, before, after)

    def _rewrite(self, documents: list[Document]) -> int:
        changed: list[Change] = []
        for document in documents:
            change = self._change(document)
            if change is not None:
                changed.append(change)
        if self.showing_diff:
            _write_diff(changed)
        elif not self.checking:
            _write_files(changed)
        self._summary(changed, len(documents))
        if changed and (self.checking or self.showing_diff):
            return 1
        return 0

    def _summary(self, changed: list[Change], total: int) -> None:
        stream = sys.stderr if self.showing_diff else sys.stdout
        if not changed:
            stream.write(f"{PREFIX}: без изменений — {total}\n")
            return
        if self.checking or self.showing_diff:
            stream.write(f"{PREFIX}: требуется форматирование — {len(changed)}\n")
        else:
            stream.write(f"{PREFIX}: отформатировано файлов — {len(changed)}\n")
        for change in changed:
            stream.write(f"  {change.rel}\n")
