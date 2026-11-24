"""mdlint.toml: severity overrides, globally and per path.

    skip = ["drafts/*"]          # files not checked at all

    [rules]
    STRUCT002 = "warning"        # or "error" / "off"

    [paths."CHAPTER_*.md"]
    STRUCT004 = "off"

Configs cascade: the one in the repository root sets the baseline, and any
mdlint.toml further down — in a work's own directory, next to its book.toml —
overrides it for that work only. Globs and skip patterns are matched against
the path relative to the config that declares them, so a lab's own file can
say `STRUCT002 = "off"` without knowing where in the tree it sits.
"""

import tomllib
from fnmatch import fnmatch
from pathlib import Path
from typing import Any, Self

from gost_lint.config_validation import ConfigError, path_rules, rule_levels, skip_patterns
from gost_lint.rules.registry import Rule

CONFIG_NAME = "mdlint.toml"


class Config:
    """Represent Config."""

    def __init__(
        self,
        config_data: dict[str, Any] | None = None,
        base: Path | None = None,
        source: Path | None = None,
    ) -> None:
        """Initialize the instance."""
        config_data = config_data or {}
        path = source or Path(CONFIG_NAME)
        self.base = base
        self.source = source
        self.globals = rule_levels(config_data.get("rules", {}), path)
        self.paths = path_rules(config_data.get("paths", {}), path)
        self.skip = skip_patterns(config_data.get("skip", []), path)

    @classmethod
    def load(cls, path: Path) -> Self:
        """Handle load."""
        try:
            with path.open("rb") as fh:
                settings = tomllib.load(fh)
        except (OSError, ValueError) as exc:
            raise ConfigError(path, str(exc)) from exc
        return cls(settings, path.parent, path)

    def override(self, rule_id: str, current: str, target: Path) -> str:
        """Level after this config had its say; `current` if it says nothing."""
        rel = self._relative(target)
        if rel is None:
            return current
        level = self.globals.get(rule_id, current)
        for pattern, rules in self.paths:
            if rule_id in rules and fnmatch(rel, pattern):
                level = rules[rule_id]
        return level

    def skips(self, target: Path) -> bool:
        """Handle skips."""
        rel = self._relative(target)
        return _matches_any(rel, self.skip)

    def _relative(self, target: Path) -> str | None:
        if self.base is None:
            return str(target)
        try:
            return str(target.relative_to(self.base))
        except ValueError:
            return None


class Chain:
    """Every mdlint.toml from the repository root down to the target file."""

    def __init__(self, root: Path, *, enabled: bool = True) -> None:
        """Initialize the instance."""
        self.root = root
        self.enabled = enabled
        self._cache: dict[Path, list[Config]] = {}

    def level_for(self, rule: Rule, target: Path) -> str:
        """Handle level for."""
        level = rule.level
        for config in self._for(target.parent):
            level = config.override(rule.id, level, target)
        return level

    def is_skipped(self, target: Path) -> bool:
        """Return whether skipped."""
        return any(config.skips(target) for config in self._for(target.parent))

    def _for(self, directory: Path) -> list[Config]:
        cached = self._cache.get(directory)
        if cached is not None:
            return cached
        configs: list[Config] = []
        if self.enabled:
            configs = _config_chain(directory, self.root)
        self._cache[directory] = configs
        return configs


def _matches_any(path: str | None, patterns: list[str]) -> bool:
    return path is not None and any(fnmatch(path, pattern) for pattern in patterns)


def _config_chain(directory: Path, root: Path) -> list[Config]:
    chain: list[Config] = []
    current = directory
    while True:
        candidate = current / CONFIG_NAME
        if candidate.exists():
            chain.append(Config.load(candidate))
        if current in {root, current.parent}:
            break
        current = current.parent
    return list(reversed(chain))
