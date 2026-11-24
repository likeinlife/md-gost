"""Geometry of Pandoc grid tables, without invoking Pandoc or adding dependencies."""

import re
from collections.abc import Sequence
from dataclasses import dataclass, field
from itertools import pairwise

START = re.compile(r"^ {0,3}\+-")
EDGE = re.compile(r"(?=(\+[-=]+\+))")
FULL_BORDER = re.compile(r"\+(?:-+\+)+")
HEADER_BORDER = re.compile(r"\+(?:=+\+)+")
HEADER_EDGE = re.compile(r"\+[=]+\+")
_MIN_BOUNDARIES = 2


@dataclass
class GridCell:
    """Represent Grid Cell."""

    row: int
    column: int
    rowspan: int
    colspan: int
    offset: int
    text: str


@dataclass
class Grid:
    """Represent Grid."""

    cells: list[GridCell] = field(default_factory=list)
    errors: list[tuple[int, int, str]] = field(default_factory=list)
    header_offset: int = 0
    columns: int = 0
    row_edges: list[int] = field(default_factory=list)
    column_edges: list[int] = field(default_factory=list)


@dataclass
class _CellAddress:
    row: int
    top: int
    column: int


def _cell_text(lines: list[str], start: int, stop: int, first_line: int, end_line: int) -> str:
    fragments = (line[start:stop] for line in lines[first_line:end_line])
    return " ".join(map(str.strip, fragments)).strip()


def parse_grid(source: Sequence[str]) -> Grid:
    """Validate a rectangular mesh; missing edges describe rectangular merged cells.

    Offsets are zero-based source line numbers within the table. The first version
    requires an explicit, full-width header separator and plain unaligned borders.
    """
    return _GridParser(source).parse()


class _GridParser:
    """Stateful parser that keeps the validation steps small and explicit."""

    def __init__(self, source: Sequence[str]) -> None:
        """Initialize the instance."""
        first_line = source[0]
        indent = len(first_line) - len(first_line.lstrip())
        self.lines = [line[indent:].rstrip() for line in source]
        self.grid = Grid()
        self.boundaries = self.grid.row_edges
        self.xs = self.grid.column_edges

    def parse(self) -> Grid:
        """Handle parse."""
        if not self._validate_lines() or not self._find_boundaries() or not self._find_header():
            return self.grid
        _GridCellReader(self).read()
        return self.grid

    def fail(self, offset: int, message: str) -> bool:
        """Handle fail."""
        self.grid.errors.append((offset, 1, message))
        return False

    def _validate_lines(self) -> bool:
        width = len(self.lines[0])
        if not FULL_BORDER.fullmatch(self.lines[0]):
            return self.fail(0, "верхняя граница grid-таблицы должна иметь вид +---+---+")
        for offset, line in enumerate(self.lines):
            if self._is_invalid_line(line, width):
                message = "границы grid-таблицы не выровнены или содержат табуляцию"
                return self.fail(offset, message)
        if not FULL_BORDER.fullmatch(self.lines[-1]):
            message = "grid-таблица не закрыта нижней границей +---+---+"
            return self.fail(len(self.lines) - 1, message)
        return True

    def _is_invalid_line(self, line: str, width: int) -> bool:
        if "\t" in line or len(line) != width:
            return True
        return line[0] not in "+|" or line[-1] not in "+|"

    def _find_boundaries(self) -> bool:
        columns: set[int] = set()
        for offset, line in enumerate(self.lines):
            for edge in EDGE.finditer(line):
                if offset not in self.boundaries:
                    self.boundaries.append(offset)
                left = edge.start()
                columns.add(left)
                columns.add(left + len(edge[1]) - 1)
        self.xs.extend(sorted(columns))
        self.grid.columns = len(self.xs) - 1
        return len(self.boundaries) >= _MIN_BOUNDARIES or self.fail(
            0,
            "grid-таблица должна содержать строки",
        )

    def _find_header(self) -> bool:
        headers = [
            boundary
            for boundary in self.boundaries
            if HEADER_BORDER.fullmatch(self.lines[boundary])
        ]
        if len(headers) != 1:
            return self.fail(
                0,
                "нужен один разделитель шапки grid-таблицы на всю ширину: +===+===+",
            )
        header = headers[0]
        if header == 0 or header == len(self.lines) - 1:
            return self.fail(
                0,
                "нужен один разделитель шапки grid-таблицы на всю ширину: +===+===+",
            )
        self.grid.header_offset = header
        for offset, line in enumerate(self.lines):
            if HEADER_EDGE.search(line) and offset != header:
                return self.fail(offset, "разделитель шапки должен проходить через все столбцы")
        return True


class _GridCellReader:
    """Read cells after the parser has validated table boundaries."""

    def __init__(self, parser: _GridParser) -> None:
        """Initialize the instance."""
        self.parser = parser
        self.lines = parser.lines
        self.grid = parser.grid
        self.boundaries = parser.boundaries
        self.xs = parser.xs
        self.occupied: set[tuple[int, int]] = set()

    def read(self) -> None:
        """Handle read."""
        for row, (top, bottom) in enumerate(pairwise(self.boundaries)):
            if not self._read_row(row, top, bottom):
                return

    def _read_row(self, row: int, top: int, bottom: int) -> bool:
        if bottom <= top + 1:
            return self.parser.fail(bottom, "между границами grid-таблицы нет строки ячеек")
        for column in range(self.grid.columns):
            address = _CellAddress(row, top, column)
            if (row, column) in self.occupied:
                continue
            bounds = self._cell_bounds(address)
            if bounds is None:
                return self.parser.fail(top, "не найдена нижняя граница объединённой ячейки")
            right, end = bounds
            if not self._make_cell(address, right, end):
                return False
        return True

    def _cell_bounds(self, address: _CellAddress) -> tuple[int, int] | None:
        right = address.column + 1
        while right < self.grid.columns:
            edge_column = self.xs[right]
            if self.lines[address.top + 1][edge_column] == "|":
                break
            right += 1
        end = address.row + 1
        while end < len(self.boundaries) and not self._horizontal(
            self.boundaries[end],
            address.column,
            right,
        ):
            end += 1
        return None if end == len(self.boundaries) else (right, end)

    def _make_cell(self, address: _CellAddress, right: int, end: int) -> bool:
        if address.top < self.grid.header_offset < self.boundaries[end]:
            return self.parser.fail(
                address.top,
                "объединение ячейки пересекает границу шапки и данных",
            )
        for row_index in range(address.top + 1, self.boundaries[end]):
            if not self._validate_cell_row(row_index, address.column, right):
                return False
        for row_index in range(address.row, end):
            for cell_index in range(address.column, right):
                if (row_index, cell_index) in self.occupied:
                    return self.parser.fail(address.top, "объединённые ячейки пересекаются")
                self.occupied.add((row_index, cell_index))
        cell_text = _cell_text(
            self.lines,
            self.xs[address.column] + 1,
            self.xs[right],
            address.top + 1,
            self.boundaries[end],
        )
        self.grid.cells.append(
            GridCell(
                address.row,
                address.column,
                end - address.row,
                right - address.column,
                address.top + 1,
                cell_text,
            ),
        )
        return True

    def _horizontal(self, row_index: int, left: int, right: int) -> bool:
        border = self.lines[row_index]
        left_edge = border[self.xs[left]]
        right_edge = border[self.xs[right]]
        if left_edge != "+" or right_edge != "+":
            return False
        start = self.xs[left] + 1
        stop = self.xs[right]
        return set(border[start:stop]) <= {"-", "=", "+"}

    def _validate_cell_row(self, row_index: int, column: int, right: int) -> bool:
        line = self.lines[row_index]
        if line[self.xs[column]] not in "|+":
            return self.parser.fail(row_index, "разорвана вертикальная граница grid-ячейки")
        if line[self.xs[right]] not in "|+":
            return self.parser.fail(row_index, "разорвана вертикальная граница grid-ячейки")
        inside = range(column + 1, right)
        if any(line[self.xs[cell_index]] in "+|" for cell_index in inside):
            return self.parser.fail(row_index, "объединённая ячейка должна быть прямоугольной")
        start = self.xs[column]
        stop = self.xs[right] + 1
        segment = line[start:stop]
        return not any(EDGE.finditer(segment)) or self.parser.fail(
            row_index,
            "внутри объединённой ячейки осталась граница",
        )
