"""Shared fixtures for the md-to-gost suite."""

import shutil
import subprocess
import zipfile
from collections.abc import Callable
from pathlib import Path

import pytest
from test_helpers import (
    ENCODING,
    MANIFEST,
    build,
)

Run = subprocess.CompletedProcess[str]
Build = tuple[Run, Path]
WorkFactory = Callable[..., Build]
BuiltFactory = Callable[[str], dict[str, str]]
needs_pandoc = pytest.mark.skipif(shutil.which("pandoc") is None, reason="pandoc не найден в PATH")


def pytest_addoption(parser: pytest.Parser) -> None:
    parser.addoption(
        "--update-golden",
        action="store_true",
        help="перезаписать tests/golden.json после намеренного изменения вывода",
    )


@pytest.fixture
def work(tmp_path: Path) -> WorkFactory:
    """Return a callable that writes and builds a one-chapter work."""
    return _WorkFactory(tmp_path)


class _WorkFactory:
    def __init__(self, directory: Path) -> None:
        self.directory = directory

    def __call__(self, body: str, manifest: str = MANIFEST, *, lint: bool = False) -> Build:
        (self.directory / "CHAPTER_1.md").write_text(body, encoding=ENCODING)
        (self.directory / "book.toml").write_text(manifest, encoding=ENCODING)
        return build(self.directory, lint=lint), self.directory


@pytest.fixture
def built(work: WorkFactory) -> BuiltFactory:
    """Return a callable that builds a snippet and reads its XML parts."""
    return _BuiltFactory(work)


class _BuiltFactory:
    def __init__(self, work: WorkFactory) -> None:
        self.work = work

    def __call__(self, body: str) -> dict[str, str]:
        completed_process, directory = self.work(body)
        assert completed_process.returncode == 0, (
            f"сборка не прошла:\n{completed_process.stdout}\n{completed_process.stderr}"
        )
        archive = zipfile.ZipFile(directory / "out.docx")
        return {
            name: archive.read(name).decode(ENCODING)
            for name in archive.namelist()
            if name.endswith(".xml")
        }
