"""Стрелки и адреса получателей в текстовой декомпозиции."""

from dataclasses import dataclass

from idef0.decomposition import Decomposition
from idef0.errors import ModelError
from idef0.text_syntax import CONTROL, INPUT, MECHANISM, OUTPUT, Statement


@dataclass(frozen=True)
class Arrow:
    """Стрелка, отличающая соседнюю цепочку от дополнительных связей."""

    line: Statement
    source: str
    target: str

    @property
    def primary(self) -> bool:
        """Прямая запись двух блоков задаёт основную цепочку."""
        return (
            self.source not in (CONTROL, MECHANISM, INPUT)
            and self.target != OUTPUT
            and "." not in self.target
        )

    def apply(self, diagram: Decomposition) -> None:
        """Добавить внешнюю или дополнительную межблочную стрелку."""
        label = self.line.label
        if self.source == INPUT:
            diagram.input(label, to=self.target, **self.line.colors)
        elif self.target == OUTPUT:
            diagram.output(label, source=self.source, **self.line.colors)
        elif self.source == CONTROL:
            diagram.control(label, to=self._destinations(), **self.line.colors)
        elif self.source == MECHANISM:
            diagram.mechanism(label, to=self._destinations(), **self.line.colors)
        else:
            self._link(diagram)

    def _destinations(self) -> str | tuple[str, ...] | None:
        if self.target == "*":
            return None
        if "," in self.target:
            return tuple(code.strip() for code in self.target.split(","))
        return self.target

    def _link(self, diagram: Decomposition) -> None:
        code, _, role = self.target.partition(".")
        line = self.line
        if role == INPUT:
            diagram.input(line.label, to=code, source=self.source, **line.colors)
        elif role == CONTROL:
            diagram.control(line.label, to=code, source=self.source, **line.colors)
        else:
            message = "для дополнительной связи укажите .input или .control"
            raise ModelError(message)
