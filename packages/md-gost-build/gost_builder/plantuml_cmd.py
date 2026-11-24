"""Locate PlantUML on macOS and Windows.

`shutil.which("plantuml")` finds a Homebrew script and a Windows
`plantuml.exe`. It does not find `plantuml.jar`: on Windows the search
only appends extensions from PATHEXT. A jar on PATH, or PLANTUML_JAR,
is started as `java -jar`. Pandoc cannot execute a `.bat` or `.cmd`
wrapper, so a wrapper is accepted only when `plantuml.jar` sits next to it.
"""

import os
import shutil
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path

from gost_builder.errors import BuildError

_JAR = "plantuml.jar"
_ENV_JAR = "PLANTUML_JAR"
_ENV_BIN = "PLANTUML"
_WRAPPERS = (".bat", ".cmd")
_PREFIX_SEP = "\n"
_NOT_FOUND = (
    "plantuml not found on PATH. "
    "Install the plantuml command, put plantuml.jar on PATH, or set PLANTUML_JAR "
    "to the jar file. https://github.com/plantuml/plantuml/releases/tag/v1.2026.10"
)


@dataclass(frozen=True)
class PlantUML:
    """Executable plus the arguments that precede PlantUML's own."""

    command: str
    prefix: tuple[str, ...] = ()

    def environment(self) -> dict[str, str]:
        """Variables the Lua filter reads instead of looking up `plantuml` itself."""
        return {
            "MD2GOST_PLANTUML": self.command,
            "MD2GOST_PLANTUML_PREFIX": _PREFIX_SEP.join(self.prefix),
        }


def resolve_plantuml(
    *,
    path: str | None = None,
    environ: Mapping[str, str] | None = None,
) -> PlantUML:
    """Find a PlantUML command or jar. `path` overrides PATH."""
    env = os.environ if environ is None else environ
    search_path = env.get("PATH", "") if path is None else path
    found = _explicit(env)
    if found is None:
        found = _on_path(search_path)
    if found is None:
        raise BuildError(_NOT_FOUND)
    return _launch(found, search_path)


def _explicit(env: Mapping[str, str]) -> Path | None:
    jar = env.get(_ENV_JAR, "").strip()
    if jar:
        return Path(jar)
    binary = env.get(_ENV_BIN, "").strip()
    if binary:
        return Path(binary)
    return None


def _on_path(search_path: str) -> Path | None:
    executable = shutil.which("plantuml", path=search_path)
    if executable is not None:
        return Path(executable)
    for entry in search_path.split(os.pathsep):
        found = _named_jar(Path(entry)) if entry else None
        if found is not None:
            return found
    return None


def _named_jar(directory: Path) -> Path | None:
    if not directory.is_dir():
        return None
    try:
        entries = list(directory.iterdir())
    except OSError:
        return None
    for entry in entries:
        if entry.is_file() and entry.name.lower() == _JAR:
            return entry
    return None


def _launch(candidate: Path, search_path: str) -> PlantUML:
    if not candidate.is_file():
        message = f"{candidate} does not exist."
        raise BuildError(message)
    jar = _jar_for(candidate)
    if jar is None:
        return PlantUML(str(candidate.resolve()))
    java = shutil.which("java", path=search_path)
    if java is None:
        message = f"java not found on PATH, needed to run {jar}."
        raise BuildError(message)
    return PlantUML(java, ("-jar", str(jar.resolve())))


def _jar_for(candidate: Path) -> Path | None:
    suffix = candidate.suffix.lower()
    if suffix == ".jar":
        return candidate
    if suffix not in _WRAPPERS:
        return None
    sibling = _named_jar(candidate.parent)
    if sibling is None:
        message = (
            f"found {candidate}, which Pandoc cannot execute. "
            f"Put {_JAR} next to it, or set {_ENV_JAR}."
        )
        raise BuildError(message)
    return sibling
