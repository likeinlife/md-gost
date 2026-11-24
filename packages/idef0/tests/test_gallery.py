"""Сквозная проверка галереи для просмотра."""

from pathlib import Path

from e2e.cases import cases
from e2e.gallery import generate
from tests.support import ensure

EXPECTED_IMAGES = 20


def test_gallery(tmp_path: Path) -> None:
    """Создать все контрольные PNG и проверить имена и формат файлов."""
    generate(tmp_path)
    actual = sorted(tmp_path.glob("*.png"))
    expected = sorted(f"{case.name}.png" for case in cases())
    ensure(condition=len(actual) == EXPECTED_IMAGES)
    ensure(condition=(tmp_path / "feedback.png").is_file())
    ensure(condition=(tmp_path / "review.png").is_file())
    ensure(condition=[path.name for path in actual] == expected)
    for path in actual:
        ensure(condition=path.read_bytes().startswith(b"\x89PNG\r\n\x1a\n"))
