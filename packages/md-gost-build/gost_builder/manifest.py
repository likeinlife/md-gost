"""Read and validate md-to-gost build manifests."""

import tomllib
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from gost_builder.errors import BuildError

DESCRIPTION = "description"
MANIFEST = "book.toml"


@dataclass(frozen=True)
class Manifest:
    """Represent Manifest."""

    chapters: list[str] = field(metadata={DESCRIPTION: "Файлы глав в порядке сборки."})
    output: str = field(default="output.docx", metadata={DESCRIPTION: "Путь выходного файла."})
    frame: bool = field(default=False, metadata={DESCRIPTION: "Параметры рамки ГОСТ."})
    toc: bool = field(default=True, metadata={DESCRIPTION: "Добавить оглавление."})
    number_sections: bool = field(default=False, metadata={DESCRIPTION: "Нумеровать разделы."})
    prefer_vector: bool = field(
        default=False,
        metadata={DESCRIPTION: "Создавать диаграммы и графики в SVG."},
    )
    page_break_before_h1: bool = field(
        default=True,
        metadata={DESCRIPTION: "Начинать заголовки первого уровня с новой страницы."},
    )


def _fail(text: str) -> None:
    raise BuildError(text)


def load_manifest(src: Path) -> Manifest:
    """Load manifest."""
    path = src / MANIFEST
    if not path.exists():
        _fail(
            f"no {MANIFEST} in {src}\n"
            f"  create one with:\n"
            f'    output = "thesis.docx"\n'
            f'    chapters = ["INTRO.md", "CHAPTER_1.md", "REFERENCES.md"]',
        )
    with path.open("rb") as source_file:
        cfg = tomllib.load(source_file)
    chapters = _validated_chapters(cfg, src)
    prefer_vector = cfg.get("prefer_vector", Manifest.prefer_vector)
    if not isinstance(prefer_vector, bool):
        _fail(f"{MANIFEST}: `prefer_vector` must be true or false")
    return Manifest(
        chapters=chapters,
        output=_validated_output(cfg),
        frame=_frame_enabled(cfg),
        toc=bool(cfg.get("toc", Manifest.toc)),
        number_sections=bool(cfg.get("number_sections", Manifest.number_sections)),
        prefer_vector=prefer_vector,
        page_break_before_h1=bool(cfg.get("page_break_before_h1", Manifest.page_break_before_h1)),
    )


def _frame_enabled(config: dict[str, Any]) -> bool:
    frame = config.get("frame")
    return isinstance(frame, dict) or bool(frame)


def _validated_chapters(config: dict[str, Any], src: Path) -> list[str]:
    chapters = config.get("chapters")
    if not chapters or not isinstance(chapters, list):
        message = f"{MANIFEST}: `chapters` must be a non-empty list"
        raise BuildError(message)
    missing = [chapter for chapter in chapters if not (src / chapter).exists()]
    if missing:
        missing_list = ", ".join(missing)
        message = f"chapters listed in {MANIFEST} not found: {missing_list}"
        raise BuildError(message)
    return chapters


def _validated_output(config: dict[str, Any]) -> str:
    output = config.get("output", Manifest.output)
    if Path(output).is_absolute() or ".." in Path(output).parts:
        message = (
            f"{MANIFEST}: `output` must be a plain name inside the chapter "
            f"directory, got {output!r}"
        )
        raise BuildError(message)
    return output
