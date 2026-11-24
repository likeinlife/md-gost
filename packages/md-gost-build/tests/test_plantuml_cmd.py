"""How a plantuml.jar or a plantuml command on PATH is chosen."""

import os
import stat
from pathlib import Path

import pytest

from gost_builder.errors import BuildError
from gost_builder.plantuml_cmd import resolve_plantuml

_PROGRAM = "plantuml.exe" if os.name == "nt" else "plantuml"
_JAVA = "java.bat" if os.name == "nt" else "java"


def _place(directory: Path, name: str, *, executable: bool = False) -> Path:
    target = directory / name
    target.write_bytes(b"")
    if executable and os.name != "nt":
        target.chmod(stat.S_IRWXU)
    return target


def test_jar_on_path_uses_java(tmp_path: Path) -> None:
    jar = _place(tmp_path, "PlantUML.jar")
    java = _place(tmp_path, _JAVA, executable=True)
    _place(tmp_path, "plantuml-1.2026.10.jar")
    launch = resolve_plantuml(path=str(tmp_path), environ={})
    assert launch.prefix == ("-jar", str(jar.resolve()))
    assert Path(launch.command) == java.resolve()


def test_executable_wins_over_a_jar(tmp_path: Path) -> None:
    program = _place(tmp_path, _PROGRAM, executable=True)
    _place(tmp_path, "plantuml.jar")
    launch = resolve_plantuml(path=str(tmp_path), environ={})
    assert Path(launch.command) == program.resolve()
    assert not launch.prefix


def test_versioned_jar_name_is_not_on_path(tmp_path: Path) -> None:
    _place(tmp_path, "plantuml-1.2026.10.jar")
    with pytest.raises(BuildError, match="plantuml not found"):
        resolve_plantuml(path=str(tmp_path), environ={})


def test_missing_file_and_missing_java(tmp_path: Path) -> None:
    with pytest.raises(BuildError, match="does not exist"):
        resolve_plantuml(path="", environ={"PLANTUML_JAR": str(tmp_path / "missing.jar")})
    _place(tmp_path, "plantuml.jar")
    with pytest.raises(BuildError, match="java not found"):
        resolve_plantuml(path=str(tmp_path), environ={})


def test_env_jar_overrides_the_command(tmp_path: Path) -> None:
    _place(tmp_path, _PROGRAM, executable=True)
    _place(tmp_path, _JAVA, executable=True)
    jar = _place(tmp_path, "custom-plantuml.jar")
    launch = resolve_plantuml(path=str(tmp_path), environ={"PLANTUML_JAR": str(jar)})
    assert launch.prefix == ("-jar", str(jar.resolve()))
