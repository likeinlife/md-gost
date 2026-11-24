"""Keep the published schema in sync with the manifest and its examples."""

import json
import tomllib
from pathlib import Path
from typing import Any

import pytest
from test_helpers import ENCODING

from generate_book_schema import SCHEMA_PATH, make_schema
from gost_builder.errors import BuildError
from gost_builder.manifest import load_manifest

Document = dict[str, Any]

ROOT = Path(__file__).resolve().parents[3]


def test_published_schema_is_current() -> None:
    assert json.loads(SCHEMA_PATH.read_text(encoding=ENCODING)) == make_schema()


def test_repository_manifests_follow_schema() -> None:
    schema = make_schema()
    for manifest_path in ROOT.rglob("book.toml"):
        if any(part.startswith(".") for part in manifest_path.relative_to(ROOT).parts):
            continue
        with manifest_path.open("rb") as manifest_file:
            manifest = tomllib.load(manifest_file)
        _check_manifest(manifest, schema, manifest_path)


def _check_manifest(manifest: Document, schema: Document, manifest_path: Path) -> None:
    assert set(schema["required"]) <= set(manifest), manifest_path
    assert set(manifest) <= set(schema["properties"]), manifest_path
    _check_chapters(manifest, manifest_path)
    assert "output" not in manifest or isinstance(manifest["output"], str), manifest_path
    _check_options(manifest, schema, manifest_path)


def _check_chapters(manifest: Document, manifest_path: Path) -> None:
    assert isinstance(manifest["chapters"], list), manifest_path
    assert manifest["chapters"], manifest_path
    assert all(isinstance(chapter, str) for chapter in manifest["chapters"]), manifest_path


def _check_options(manifest: Document, schema: Document, manifest_path: Path) -> None:
    for name in ("toc", "number_sections", "page_break_before_h1", "prefer_vector"):
        assert name not in manifest or isinstance(manifest[name], bool), manifest_path
    if isinstance(manifest.get("frame"), dict):
        frame_schema = schema["properties"]["frame"]["oneOf"][1]
        assert set(manifest["frame"]) <= set(frame_schema["properties"]), manifest_path


def test_empty_frame_table_enables_frame(tmp_path: Path) -> None:
    (tmp_path / "chapter.md").write_text("# Тест\n", encoding=ENCODING)
    (tmp_path / "book.toml").write_text('chapters = ["chapter.md"]\n[frame]\n', encoding=ENCODING)
    assert load_manifest(tmp_path).frame


def test_vector_preference_requires_boolean(tmp_path: Path) -> None:
    (tmp_path / "chapter.md").write_text("# Тест\n", encoding=ENCODING)
    (tmp_path / "book.toml").write_text(
        'chapters = ["chapter.md"]\nprefer_vector = "false"\n',
        encoding=ENCODING,
    )
    with pytest.raises(BuildError, match="prefer_vector"):
        load_manifest(tmp_path)
