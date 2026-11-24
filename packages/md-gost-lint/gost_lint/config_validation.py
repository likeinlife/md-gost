"""Validate TOML values before applying them to lint findings."""

from pathlib import Path
from typing import Any

LEVELS = ("error", "warning", "off")
RuleLevels = dict[str, str]
PathRules = list[tuple[str, RuleLevels]]


class ConfigError(ValueError):
    """A malformed configuration file with the path that owns the error."""

    def __init__(self, path: Path, message: str) -> None:
        """Initialize the instance."""
        super().__init__(f"{path}: {message}")
        self.path = path


def rule_levels(settings: Any, path: Path) -> RuleLevels:
    """Handle rule levels."""
    if not isinstance(settings, dict):
        raise ConfigError(path, "rules должен быть таблицей уровней правил")
    for rule_id, level in settings.items():
        if level not in LEVELS:
            expected = ", ".join(LEVELS)
            raise ConfigError(
                path,
                f"bad level {level!r} for {rule_id}, expected one of {expected}",
            )
    return settings


def path_rules(settings: Any, path: Path) -> PathRules:
    """Handle path rules."""
    if not isinstance(settings, dict):
        raise ConfigError(path, "paths должен быть таблицей шаблонов путей")
    return [(glob, rule_levels(levels, path)) for glob, levels in settings.items()]


def skip_patterns(settings: Any, path: Path) -> list[str]:
    """Handle skip patterns."""
    message = "skip должен быть списком строковых шаблонов путей"
    if not isinstance(settings, list):
        raise ConfigError(path, message)
    if not all(isinstance(pattern, str) for pattern in settings):
        raise ConfigError(path, message)
    return settings
