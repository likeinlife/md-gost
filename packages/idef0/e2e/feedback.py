"""Выпуск ПО с обратной связью от испытаний и эксплуатации."""

from idef0 import Arrow, Block, Link, Waterfall

REQUIREMENTS = "A1"
DESIGN = "A2"
DEVELOPMENT = "A3"
TESTING = "A4"
RELEASE = "A5"
SUPPORT = "A6"


def feedback() -> Waterfall:
    """Построить модель выпуска с короткими и длинными обратными связями."""
    return Waterfall(
        blocks=[
            Block(REQUIREMENTS, "Уточнить\nтребования"),
            Block(DESIGN, "Спроектировать\nмодуль"),
            Block(DEVELOPMENT, "Реализовать\nизменения"),
            Block(TESTING, "Испытать\nсборку"),
            Block(RELEASE, "Выпустить\nверсию"),
            Block(SUPPORT, "Разобрать\nобращения"),
        ],
        chain=["Требования", "Проект модуля", "Сборка", "Проверенная сборка", "Описание версии"],
        inputs={REQUIREMENTS: "Заявка", SUPPORT: "Обращения"},
        outputs={RELEASE: "Версия ПО", SUPPORT: "Ответы"},
        controls=[Arrow("Политика безопасности"), Arrow("Окно выпуска", to=RELEASE)],
        mechanisms=[
            Arrow("Команда продукта"),
            Arrow("Сборочный стенд", to=(DEVELOPMENT, TESTING)),
        ],
        links=[
            Link(DESIGN, RELEASE, "Схема развёртывания", role="input"),
            Link(TESTING, DESIGN, "Журналы сбоев", role="input"),
            Link(SUPPORT, REQUIREMENTS, "Запросы на изменение", role="input"),
            Link(REQUIREMENTS, TESTING, "Критерии приёмки", role="control"),
            Link(TESTING, DEVELOPMENT, "Замечания к сборке", role="control"),
            Link(SUPPORT, DESIGN, "Ограничения нагрузки", role="control"),
        ],
    )
