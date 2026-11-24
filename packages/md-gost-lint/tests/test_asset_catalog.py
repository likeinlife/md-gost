"""Check the search depth, reuse and invalidation of the work's path index."""

from pathlib import Path
from unittest.mock import patch

from gost_lint.lsp.asset_catalog import Directory
from gost_lint.lsp.completion_files import file_names, warm_file_catalog

FIGURES = "figures/"
MODEL = "figures/model"
OVERVIEW = "figures/model/overview.PNG"
DETAIL = "figures/model/private/detail.svg"
CHART = "figures/chart.py"
IMAGE = "logo.jpg"
SCRIPT = frozenset((".py",))


def _create(folder: Path, name: str) -> Path:
    path = folder / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.touch()
    return path


def _images(root: Path, prefix: str = "") -> set[str]:
    return set(file_names(prefix, root, root, image=True))


def test_direct_paths_for_two_levels_only(tmp_path: Path) -> None:
    root = tmp_path.resolve()
    for name in (IMAGE, OVERVIEW, DETAIL, CHART, "figures/note.txt"):
        _create(root, name)
    choices = list(file_names("", root, root, image=True))
    assert choices.count(IMAGE) == 1
    assert set(choices) == {IMAGE, OVERVIEW, CHART, FIGURES}
    assert _images(root, f"{MODEL}/private/") == {DETAIL}
    scripts = file_names("", root, root, image=False, suffixes=SCRIPT)
    assert set(scripts) == {FIGURES, CHART}


def test_warm_index_rereads_only_changed_folder(tmp_path: Path) -> None:
    root = tmp_path.resolve()
    before = _create(root, OVERVIEW)
    with patch.object(Directory, "read", wraps=Directory.read) as scan:
        warm_file_catalog(root)
        cached_scans = 3
        assert scan.call_count == cached_scans
        assert OVERVIEW in _images(root)
        assert scan.call_count == cached_scans
        before.rename(before.with_name("new.png"))
        assert _images(root) == {FIGURES, f"{MODEL}/new.png"}
        scans_after_rename = 4
        assert scan.call_count == scans_after_rename


def test_new_and_removed_subdirectories(tmp_path: Path) -> None:
    root = tmp_path.resolve()
    warm_file_catalog(root)
    added = _create(root, OVERVIEW)
    assert OVERVIEW in _images(root)
    added.unlink()
    added.parent.rmdir()
    assert _images(root) == {FIGURES}


def test_external_and_hidden_paths(tmp_path: Path) -> None:
    root = tmp_path.resolve() / "book"
    _create(root, IMAGE)
    external = _create(root.parent, "outside/secret.png")
    _create(root, ".md-to-gost/generated.png")
    (root / "outside").symlink_to(external.parent)
    (root / "escape.png").symlink_to(external)
    (root / "relative.png").symlink_to(IMAGE)
    assert _images(root) == {IMAGE, "relative.png"}
    assert not _images(root, "outside/")
    assert not _images(root, ".md-to-gost/")


def test_internal_folder_symlink_can_be_browsed(tmp_path: Path) -> None:
    root = tmp_path.resolve()
    _create(root, OVERVIEW)
    (root / "alias").symlink_to(MODEL)
    (root / MODEL / "cycle").symlink_to(root)
    assert _images(root) == {OVERVIEW, FIGURES, "alias/"}
    assert _images(root, "alias/") == {"alias/overview.PNG", "alias/cycle/"}
