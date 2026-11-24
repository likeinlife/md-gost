"""Check the build prerequisites before invoking Pandoc."""

import re
import shutil
import sys
from dataclasses import dataclass
from pathlib import Path

import pypandoc

from gost_builder.errors import BuildError
from gost_builder.manifest import Manifest
from gost_builder.plantuml_cmd import PlantUML, resolve_plantuml

DIAGRAM = re.compile(r"```\s*\{?\.?plantuml|\.(?:puml|iuml)\)")
MANUAL_NUMBER = re.compile(r"^#{1,6}\s+(?:Глава\s+)?\d+(?:\.\d+)*\.?\s+\S")
_PANDOC_HINT = (
    "pandoc not found. Install 3.9.x from https://pandoc.org/installing.html. "
    "Windows: winget install --source winget --exact --id JohnMacFarlane.Pandoc. "
    'Or: python -c "import pypandoc; pypandoc.download_pandoc()".'
)
_GRAPHVIZ_HINT = (
    "warning: dot (Graphviz) was not found on PATH. "
    "PlantUML needs it for diagrams it does not lay out itself. "
    "https://graphviz.org/download/\n"
)


@dataclass(frozen=True)
class Preflight:
    """Tools the rest of the build is allowed to call."""

    pandoc: str
    plantuml: PlantUML | None = None


def preflight(src: Path, manifest: Manifest) -> Preflight:
    """Fail early, with a usable message, instead of deep inside pandoc."""
    pandoc = _pandoc()
    plantuml = None
    if _has_diagrams(src, manifest.chapters):
        plantuml = resolve_plantuml()
        _warn_graphviz()
    if manifest.number_sections:
        _check_manual_numbers(src, manifest.chapters)
    return Preflight(pandoc=pandoc, plantuml=plantuml)


def _pandoc() -> str:
    try:
        return pypandoc.get_pandoc_path()
    except OSError as exc:
        raise BuildError(_PANDOC_HINT) from exc


def _warn_graphviz() -> None:
    if shutil.which("dot") is not None:
        return
    sys.stderr.write(_GRAPHVIZ_HINT)


def _has_diagrams(src: Path, chapters: list[str]) -> bool:
    for chapter in chapters:
        chapter_text = (src / chapter).read_text(encoding="utf-8")
        if DIAGRAM.search(chapter_text):
            return True
    return False


def _check_manual_numbers(src: Path, chapters: list[str]) -> None:
    """With number_sections on, a hand-typed number would be doubled.

    pandoc numbers every heading it sees, so «## 1.2 Название» comes out as
    «1.2 1.2 Название». Nothing downstream can tell the two numbers apart, so
    this is caught here rather than found in the .docx.
    """
    found: list[str] = []
    for name in chapters:
        chapter_text = (src / name).read_text(encoding="utf-8")
        for number, line in enumerate(chapter_text.splitlines(), 1):
            if MANUAL_NUMBER.match(line):
                found.append(f"  {name}:{number}: {line.strip()}")
    if found:
        raise BuildError(
            "number_sections is on, but these headings already carry a number:\n"
            + "\n".join(found)
            + "\n  Drop the numbers from the source — the build assigns them. A "
            "section that must stay unnumbered is marked `{-}`.",
        )
