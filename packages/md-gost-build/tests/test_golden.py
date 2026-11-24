"""Golden test: example/ must build into exactly the document it built before.

Run with --update-golden after an intended change to the output.
"""

import json
import shutil
from typing import Any

import pytest
from conftest import needs_pandoc
from test_helpers import EXAMPLE, GOLDEN, build, snapshot

pytestmark = [needs_pandoc, pytest.mark.build]


@pytest.fixture(scope="module")
def example_snapshot(tmp_path_factory: pytest.TempPathFactory) -> dict[str, Any]:
    """Собирает копию example/, а не сам каталог.

    example.docx — файл под контролем версий; прогон тестов не должен его
    переписывать, иначе любой запуск pytest оставляет за собой грязное дерево.
    """
    work = tmp_path_factory.mktemp("golden") / "example"
    shutil.copytree(EXAMPLE, work, ignore=shutil.ignore_patterns(".md-to-gost", "example.docx"))
    completed_process = build(work)
    assert completed_process.returncode == 0, (
        f"example/ не собрался:\n{completed_process.stdout}\n{completed_process.stderr}"
    )
    return snapshot(work / "example.docx")


def test_matches_golden(example_snapshot: dict[str, Any], request: pytest.FixtureRequest) -> None:
    if request.config.getoption("--update-golden"):
        GOLDEN.parent.mkdir(exist_ok=True)
        GOLDEN.write_text(
            json.dumps(example_snapshot, ensure_ascii=False, indent=1),
            encoding="utf-8",
        )
        pytest.skip(f"golden обновлён: {GOLDEN}")

    assert GOLDEN.exists(), "нет tests/golden.json; запустите с --update-golden"
    want = json.loads(GOLDEN.read_text(encoding="utf-8"))
    for key in sorted(set(want) | set(example_snapshot)):
        assert example_snapshot.get(key) == want.get(key), f"расхождение в {key!r}"
