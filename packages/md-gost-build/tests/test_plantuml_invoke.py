"""Wrappers, explicit paths, and the arguments passed to the Lua filter."""

import os
import stat
from pathlib import Path

import pytest

from gost_builder.errors import BuildError
from gost_builder.plantuml_cmd import PlantUML, resolve_plantuml

_JAVA = "java.bat" if os.name == "nt" else "java"
_WHICH = "gost_builder.plantuml_cmd.shutil.which"
_CMD = "plantuml"


def _place(directory: Path, name: str, *, executable: bool = False) -> Path:
    target = directory / name
    target.write_bytes(b"")
    if executable and os.name != "nt":
        target.chmod(stat.S_IRWXU)
    return target


class _Which:
    def __init__(self, program: str, java: str = "") -> None:
        self.program = program
        self.java = java

    def __call__(self, name: str, path: str | None = None) -> str | None:
        if path is None:
            return None
        if name == _CMD:
            return self.program
        if name == "java" and self.java:
            return self.java
        return None


def test_wrapper_uses_the_jar_beside_it(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    wrapper = _place(tmp_path, "plantuml.bat")
    jar = _place(tmp_path, "plantuml.jar")
    java = _place(tmp_path, _JAVA, executable=True)
    lookup = _Which(str(wrapper), str(java))
    monkeypatch.setattr(_WHICH, lookup)
    launch = resolve_plantuml(path=str(tmp_path), environ={})
    assert launch.prefix == ("-jar", str(jar.resolve()))
    assert Path(launch.command) == java.resolve()


def test_wrapper_without_a_jar_is_rejected(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    wrapper = _place(tmp_path, "plantuml.cmd")
    monkeypatch.setattr(_WHICH, _Which(str(wrapper)))
    with pytest.raises(BuildError, match="Pandoc cannot execute"):
        resolve_plantuml(path=str(tmp_path), environ={})


def test_env_command_can_point_at_a_native_binary(tmp_path: Path) -> None:
    binary = _place(tmp_path, "plantuml-native.exe")
    launch = resolve_plantuml(path="", environ={"PLANTUML": str(binary)})
    assert Path(launch.command) == binary.resolve()
    assert not launch.prefix


def test_posix_script_is_used_when_which_finds_it(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    script = tmp_path / _CMD
    script.write_text("#!/bin/sh\n", encoding="utf-8")
    monkeypatch.setattr(_WHICH, _Which(str(script)))
    launch = resolve_plantuml(path="", environ={})
    assert Path(launch.command) == script.resolve()
    assert not launch.prefix


def test_environment_keeps_a_path_with_spaces() -> None:
    jar = r"K:\user\Apps\Plantuml\plantuml.jar"
    launch = PlantUML(r"C:\Program Files\Java\java.exe", ("-jar", jar))
    assert launch.environment()["MD2GOST_PLANTUML_PREFIX"] == f"-jar\n{jar}"
