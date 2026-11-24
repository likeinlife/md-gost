"""Paths for the md-gost command tests."""

import shutil
from collections.abc import Iterator
from pathlib import Path

import pytest

ENTRY = Path(__file__).resolve().parents[1]
TOOLS = ENTRY.parent
REPO = TOOLS.parent
LINT = TOOLS / "md-gost-lint"
FIXTURES = LINT / "tests" / "fixtures"


@pytest.fixture
def fixtures() -> Path:
    return FIXTURES


@pytest.fixture
def sandbox(tmp_path: Path) -> Iterator[Path]:
    """A directory inside the repository — the config cascade needs a real path."""
    workdir = ENTRY / ".pytest-sandbox"
    workdir.mkdir(exist_ok=True)
    target = workdir / tmp_path.name
    shutil.rmtree(target, ignore_errors=True)
    target.mkdir()
    yield target
    shutil.rmtree(target, ignore_errors=True)
    if not any(workdir.iterdir()):
        workdir.rmdir()
