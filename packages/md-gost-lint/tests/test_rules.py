"""Each fixture must produce exactly one known set of rules.

Exactly — not «at least»: a new rule that starts firing on old text shows up
here as an unexpected id, which is the whole point of pinning the set.
"""

from pathlib import Path
from types import MappingProxyType

import pytest
from conftest import rules_found, run_lint

NO_CONFIG = "--no-config"
UTF8 = "utf-8"
SECTION_END_FILE = "section_end.md"
RULE_REF005 = "REF005"
DIAGRAMS_DIR = "diagrams"


def _no_config_rules(target: Path) -> set[str]:
    return rules_found(target, NO_CONFIG)


def _file_rules(target: Path) -> set[str]:
    return _no_config_rules(target)


CASES = MappingProxyType(
    {
        SECTION_END_FILE: {"STRUCT001", "STRUCT002", "STRUCT003", RULE_REF005},
        "refs.md": {"REF001", "REF002", "REF003", RULE_REF005, "REF007"},
        "style.md": {"STYLE001", "STYLE002", "STYLE003", "STYLE004", "STYLE005", "STYLE006"},
        "typo.md": {"TYPO001", "TYPO002", "TYPO003", "TYPO004", "TYPO005", "TYPO006"},
        "headings.md": {"STRUCT008", "STRUCT009"},
        "formulas.md": {"EQ001", "EQ002", "EQ003", "EQ004", RULE_REF005},
        "listings.md": {"LST001", "LST002", "LST003", RULE_REF005, "REF007", "REF010"},
        "clean.md": set(),
        "grid.md": set(),
        "grid_invalid.md": {"STYLE005"},
        "work_lab": {"STRUCT007"},
        "work_diagrams": {"REF010", "REF011"},
    },
)


class TestGroup1:
    @pytest.mark.parametrize(("name", "expected"), sorted(CASES.items()))
    def test_fixture_rules(self, fixtures: Path, name: str, expected: set[str]) -> None:
        assert _no_config_rules(fixtures / name) == expected

    def test_clean_fixture_is_silent(self, fixtures: Path) -> None:
        """The positive case: correct text must produce nothing at all."""
        assert _no_config_rules(fixtures / "clean.md") == set()

    def test_diagram_body_is_not_scanned(self, sandbox: Path) -> None:
        """Quotes and bold inside a ```plantuml block are markup, not prose."""
        chapter = sandbox / "diagram.md"
        chapter.write_text(
            "# Глава 1. Диаграмма\n\n"
            "## 1.1 Схема\n\n"
            "Схема взаимодействия приведена на рисунке [@fig:seq].\n\n"
            '```{.plantuml #fig:seq caption="Диаграмма последовательности"}\n'
            'actor "Пользователь" as U\n'
            "U -> System : **запрос**\n"
            "```\n\n"
            "Схема показывает, что запрос проходит через единственную точку входа.\n",
            encoding=UTF8,
        )
        assert _file_rules(chapter) == set()

    def test_captioned_code_block_is_an_attachment(self, sandbox: Path) -> None:
        """Листинг — вложение: раздел им не заканчивается, ссылка на него нужна."""
        chapter = sandbox / "listing_end.md"
        chapter.write_text(
            "# Глава 1. Реализация\n\n"
            "## 1.1 Обработчик\n\n"
            "Точка входа приведена в листинге [@lst:h].\n\n"
            '```{.python #lst:h caption="Обработчик"}\n'
            "def handle():\n"
            "    pass\n"
            "```\n",
            encoding=UTF8,
        )
        assert "STRUCT001" in _no_config_rules(chapter)

    def test_plain_code_block_is_not_an_attachment(self, sandbox: Path) -> None:
        """Блок без подписи — часть текста: ни номера, ни требований вложения."""
        chapter = sandbox / "plain_code.md"
        chapter.write_text(
            "# Глава 1. Настройка\n\n"
            "## 1.1 Команда запуска\n\n"
            "Сборка запускается одной командой:\n\n"
            "```\n"
            "./md-to-gost work/\n"
            "```\n\n"
            "Команда собирает документ целиком.\n",
            encoding=UTF8,
        )
        assert _file_rules(chapter) == set()

    def test_section_may_not_end_with_a_formula(self, sandbox: Path) -> None:
        """Формула — такое же вложение, как таблица: после неё нужен вывод."""
        chapter = sandbox / "formula_end.md"
        chapter.write_text(
            "# Глава 1. Оценка\n\n"
            "## 1.1 Показатель\n\n"
            "Показатель считается по формуле [@eq:k].\n\n"
            "<!-- #eq:k -->\n\n"
            "$$K = a / b$$\n",
            encoding=UTF8,
        )
        assert "STRUCT001" in _no_config_rules(chapter)


class TestGroup2:
    def test_formula_with_its_marker_is_silent(self, sandbox: Path) -> None:
        """Маркер, формула, экспликация, вывод — так это и пишется."""
        chapter = sandbox / "formula_ok.md"
        lines = (
            "# Глава 1. Оценка",
            "",
            "## 1.1 Показатель",
            "",
            "Интегральный показатель вычисляется по формуле [@eq:k].",
            "",
            "<!-- #eq:k -->",
            "",
            r"$$K = \frac{a}{b}$$",
            "",
            "где $a$ — сумма взвешенных оценок;",
            "$b$ — сумма весов.",
            "",
            "Значение показателя сравнивается с пороговым.",
            "",
        )
        chapter.write_text("\n".join(lines), encoding=UTF8)
        assert _no_config_rules(chapter) == set()

    def test_table_marker_must_touch_the_table(self, sandbox: Path) -> None:
        chapter = sandbox / "marker.md"
        chapter.write_text(
            "# Глава 1. Таблица\n\n"
            "## 1.1 Данные\n\n"
            "Состав приведён в таблице [@tbl:x].\n\n"
            "<!-- #tbl:x Состав -->\n\n"
            "Абзац, вклинившийся между маркером и таблицей.\n\n"
            "| А | Б |\n|---|---|\n| 1 | 2 |\n\n"
            "Закрывающий абзац.\n",
            encoding=UTF8,
        )
        assert "REF002" in _no_config_rules(chapter)

    def test_diagram_target_checks_its_includes(self, fixtures: Path) -> None:
        """A .puml passed directly is linted as its include chain."""
        target = fixtures / "work_diagrams" / DIAGRAMS_DIR / "broken.puml"
        assert _no_config_rules(target) == {"REF011"}

    def test_existing_diagram_and_include_are_silent(self, sandbox: Path) -> None:
        (sandbox / DIAGRAMS_DIR).mkdir()
        (sandbox / DIAGRAMS_DIR / "style.iuml").write_text(
            "skinparam monochrome true\n",
            encoding=UTF8,
        )
        (sandbox / DIAGRAMS_DIR / "scheme.puml").write_text(
            "@startuml\n!include style.iuml\nA -> B\n@enduml\n",
            encoding=UTF8,
        )
        (sandbox / "book.toml").write_text(
            'output = "out.docx"\nchapters = ["CHAPTER_1.md"]\n',
            encoding=UTF8,
        )
        (sandbox / "CHAPTER_1.md").write_text(
            "# Глава 1. Схема\n\n## 1.1 Схема\n\n"
            "Обмен показан на рисунке [@fig:s].\n\n"
            "![Схема обмена](diagrams/scheme.puml){#fig:s}\n\n"
            "Схема показывает единственный канал обмена.\n",
            encoding=UTF8,
        )
        assert rules_found(sandbox, NO_CONFIG) == set()

    def test_numbering_column_is_allowed(self, sandbox: Path) -> None:
        """Номер в собственной колонке — это как раз то, чего требует STYLE006."""
        chapter = sandbox / "numbered.md"
        chapter.write_text(
            "# Глава 1. Стадии\n\n"
            "## 1.1 Состав\n\n"
            "Стадии приведены в таблице [@tbl:s].\n\n"
            "<!-- #tbl:s Стадии работ -->\n\n"
            "| № | Стадия | Содержание |\n|---|---|---|\n"
            "| 1 | Первая | Обследование |\n"
            "| 2 | Вторая | Проектирование |\n\n"
            "Закрывающий абзац раздела.\n",
            encoding=UTF8,
        )
        assert _no_config_rules(chapter) == set()

    def test_digit_codes_are_not_numbering(self, sandbox: Path) -> None:
        """«1.1 Подсистема» в ячейке — обозначение, а не сквозная нумерация строк."""
        chapter = sandbox / "codes.md"
        chapter.write_text(
            "# Глава 1. Обозначения\n\n"
            "## 1.1 Состав\n\n"
            "Коды приведены в таблице [@tbl:c].\n\n"
            "<!-- #tbl:c Коды подсистем -->\n\n"
            "| Код | Назначение |\n|---|---|\n"
            "| 4. Эскизный проект по ГОСТ | Предварительные решения |\n"
            "| 7. Ввод в действие | Монтаж и пусконаладка |\n\n"
            "Закрывающий абзац раздела.\n",
            encoding=UTF8,
        )
        assert "STYLE006" not in _no_config_rules(chapter)


class TestGroup3:
    def test_structural_titles_keep_place(self, sandbox: Path) -> None:
        """Нумеруется только раздел работы; «Введение» и «Заключение» — нет."""
        chapter = sandbox / "intro.md"
        chapter.write_text(
            "# Введение\n\n"
            "Работа посвящена управлению знаниями в проектной организации.\n\n"
            "## 1 Постановка задачи\n\n"
            "Задача состоит в выборе средств автоматизации.\n\n"
            "## Заключение\n\n"
            "Задача решена, средства выбраны.\n",
            encoding=UTF8,
        )
        assert "STRUCT009" not in _no_config_rules(chapter)

    def test_em_dash_opens_a_line_but_not_a_list(self, sandbox: Path) -> None:
        """Тире в начале строки ловится; тире внутри строки и дефисный список — нет."""
        chapter = sandbox / "dash.md"
        chapter.write_text(
            "# Глава 1. Перечни\n\n"
            "## 1.1 Состав\n\n"
            "Состав работ перечислен ниже.\n\n"
            "— первый пункт;\n"
            "— второй пункт.\n\n"
            "Тот же перечень дефисом:\n\n"
            "- первый пункт;\n"
            "- второй пункт.\n\n"
            "Перечень закрыт, а тире — вот оно — внутри строки правилу не мешает.\n",
            encoding=UTF8,
        )
        _, issues = run_lint(chapter, NO_CONFIG)
        typo_lines = [issue["line"] for issue in issues if issue["rule"] == "TYPO006"]
        assert typo_lines == [7, 8]
