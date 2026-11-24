"""mdlint.toml: cascade, path globs, validation."""

from pathlib import Path

import pytest
from conftest import rules_found

from gost_lint.config import Config

SECTION_END = "section_end.md"
UTF8 = "utf-8"
RULE_STRUCT001 = "STRUCT001"
RULE_STRUCT002 = "STRUCT002"
CONFIG_FILE = "mdlint.toml"


def test_local_config_overrides_default(fixtures: Path, sandbox: Path) -> None:
    chapter = sandbox / "chapter.md"
    chapter.write_text((fixtures / SECTION_END).read_text(encoding=UTF8), encoding=UTF8)
    assert RULE_STRUCT002 in rules_found(chapter)

    (sandbox / CONFIG_FILE).write_text(f'[rules]\n{RULE_STRUCT002} = "off"\n', encoding=UTF8)
    after = rules_found(chapter)
    assert RULE_STRUCT002 not in after
    assert RULE_STRUCT001 in after, "локальный конфиг не должен гасить прочие правила"


def test_path_glob_is_relative_to_the_config(fixtures: Path, sandbox: Path) -> None:
    chapter = sandbox / "CHAPTER_9.md"
    chapter.write_text((fixtures / SECTION_END).read_text(encoding=UTF8), encoding=UTF8)
    settings = f'[paths."CHAPTER_*.md"]\n{RULE_STRUCT001} = "off"\n'
    (sandbox / CONFIG_FILE).write_text(settings, encoding=UTF8)
    assert RULE_STRUCT001 not in rules_found(chapter)


def test_skip_excludes_a_file(fixtures: Path, sandbox: Path) -> None:
    chapter = sandbox / "draft.md"
    chapter.write_text((fixtures / SECTION_END).read_text(encoding=UTF8), encoding=UTF8)
    (sandbox / CONFIG_FILE).write_text('skip = ["draft.md"]\n', encoding=UTF8)
    assert rules_found(chapter) == set()


def test_no_config_ignores_the_cascade(fixtures: Path, sandbox: Path) -> None:
    chapter = sandbox / "chapter.md"
    chapter.write_text((fixtures / SECTION_END).read_text(encoding=UTF8), encoding=UTF8)
    (sandbox / CONFIG_FILE).write_text(f'[rules]\n{RULE_STRUCT002} = "off"\n', encoding=UTF8)
    assert RULE_STRUCT002 in rules_found(chapter, "--no-config")


def test_bad_level_is_rejected() -> None:
    with pytest.raises(ValueError, match="STRUCT001"):
        Config({"rules": {"STRUCT001": "fatal"}})
