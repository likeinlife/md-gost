"""Build PlantUML fixtures and verify their document output."""

import zipfile
from pathlib import Path

from test_helpers import ENCODING, MANIFEST, W_T, build


def build_diagram(tmp_path: Path, *, fragment: bool) -> None:
    image, marker = _diagram_inputs(tmp_path, fragment=fragment)
    chapter = f"# Глава 1. Схема\n\n{image}\n\nОбмен показан на рисунке [@fig:{marker}].\n"
    (tmp_path / "CHAPTER_1.md").write_text(chapter, encoding=ENCODING)
    (tmp_path / "book.toml").write_text(MANIFEST, encoding=ENCODING)
    completed_process = build(tmp_path)
    assert completed_process.returncode == 0, (
        f"{completed_process.stdout}\n{completed_process.stderr}"
    )


def _diagram_inputs(tmp_path: Path, *, fragment: bool) -> tuple[str, str]:
    if fragment:
        _write_fragment(tmp_path)
        return '![](steps.iuml){#fig:steps caption="Алгоритм обработки"}', "steps"
    _write_diagram_file(tmp_path)
    return "![Схема обмена](diagrams/flow.puml){#fig:flow}", "flow"


def _write_fragment(tmp_path: Path) -> None:
    (tmp_path / "steps.iuml").write_text("start\n:шаг;\nstop\n", encoding=ENCODING)


def _write_diagram_file(tmp_path: Path) -> None:
    diagram_dir = tmp_path / "diagrams"
    diagram_dir.mkdir()
    (diagram_dir / "style.iuml").write_text("skinparam monochrome true\n", encoding=ENCODING)
    (diagram_dir / "flow.puml").write_text(
        "@startuml\n!include style.iuml\nAlice -> Bob : запрос\n@enduml\n",
        encoding=ENCODING,
    )


def assert_diagram(tmp_path: Path, caption: str, reference: str) -> None:
    with zipfile.ZipFile(tmp_path / "out.docx") as archive:
        media = any(name.startswith("word/media/") for name in archive.namelist())
        xml = archive.read("word/document.xml").decode(ENCODING)
    assert media, "диаграмма не попала в документ"
    text = "".join(W_T.findall(xml))
    assert f"Рисунок 1 – {caption}" in text
    assert reference in text
