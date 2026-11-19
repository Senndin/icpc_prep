from dataclasses import dataclass


@dataclass
class ProblemCell:
    """Клітинка таблиці результатів: стан однієї задачі для однієї команди."""

    letter: str
    solved: bool = False
    wrong_attempts: int = 0
    solve_minute: int = 0
    first_to_solve: bool = False

    @property
    def penalty(self):
        """
        Штрафний час за задачу за правилами ICPC.

        :return: хвилини розв'язання + 20 хв за кожну невдалу спробу
        """
        return self.solve_minute + 20 * self.wrong_attempts if self.solved else 0

    @property
    def label(self):
        """
        Позначення в таблиці: «+», «+2», «-3» або порожньо.

        :return: рядок для відображення
        """
        if self.solved:
            return f"+{self.wrong_attempts}" if self.wrong_attempts else "+"
        return f"-{self.wrong_attempts}" if self.wrong_attempts else ""
