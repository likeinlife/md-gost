from pathlib import Path

import pytest
from conftest import needs_pandoc
from image_diagrams_helpers import assert_diagram, build_diagram
from image_helpers import assert_large_image_fits, build_large_image

pytestmark = [needs_pandoc, pytest.mark.build]


def test_oversized_image_is_scaled_to_page(tmp_path: Path) -> None:
    """A picture taller than the page is scaled down, aspect ratio kept."""
    completed_process = build_large_image(tmp_path)
    assert completed_process.returncode == 0, (
        f"{completed_process.stdout}\n{completed_process.stderr}"
    )
    assert_large_image_fits(tmp_path)


def test_diagram_file_keeps_its_includes(tmp_path: Path) -> None:
    """![](x.puml) renders like an inline fence, and keeps its own !include."""
    build_diagram(tmp_path, fragment=False)
    assert_diagram(tmp_path, "Схема обмена", "на рисунке 1.")


def test_diagram_fragment_is_wrapped(tmp_path: Path) -> None:
    """A bare .iuml fragment is wrapped and its caption is rendered."""
    build_diagram(tmp_path, fragment=True)
    assert_diagram(tmp_path, "Алгоритм обработки", "на рисунке 1.")
