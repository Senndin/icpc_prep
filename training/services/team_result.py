from dataclasses import dataclass, field


@dataclass
class TeamResult:
    """Рядок таблиці результатів тренування для однієї команди."""

    team: object
    cells: list = field(default_factory=list)
    rank: int = 0

    @property
    def solved(self):
        """:return: кількість розв'язаних задач"""
        return sum(1 for cell in self.cells if cell.solved)

    @property
    def penalty(self):
        """:return: сумарний штрафний час у хвилинах"""
        return sum(cell.penalty for cell in self.cells)

    @property
    def last_solve_minute(self):
        """:return: хвилина останньої зарахованої задачі (додатковий критерій)"""
        return max((cell.solve_minute for cell in self.cells if cell.solved), default=0)

    def sort_key(self):
        """
        Ключ сортування за правилами ICPC.

        :return: кортеж (-розв'язано, штраф, час останньої задачі)
        """
        return (-self.solved, self.penalty, self.last_solve_minute)
