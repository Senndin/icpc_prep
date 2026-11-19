from collections import defaultdict

from training.models import Attempt

from .problem_cell import ProblemCell
from .team_result import TeamResult


class StandingsCalculator:
    """
    Обчислення таблиці результатів тренування за правилами ICPC.

    Команди впорядковуються за кількістю розв'язаних задач (спадання),
    потім за штрафним часом (зростання).
    """

    def __init__(self, training):
        """
        :param training: тренування, для якого будується таблиця
        """
        self._training = training

    def _load_attempts(self, teams, problems):
        """
        Групує спроби учасників за (команда, задача) у хронологічному порядку.

        :param teams: список команд
        :param problems: список задач
        :return: словник {(id команди, id задачі): [спроби]}
        """
        member_team = {}
        for team in teams:
            for member in team.members.all():
                member_team[member.pk] = team.pk
        attempts = Attempt.objects.filter(
            user_id__in=member_team.keys(),
            problem__in=problems,
            submitted_at__gte=self._training.start_at,
            submitted_at__lte=self._training.end_at,
        ).order_by("submitted_at")
        grouped = defaultdict(list)
        for attempt in attempts:
            grouped[(member_team[attempt.user_id], attempt.problem_id)].append(attempt)
        return grouped

    def _build_cell(self, letter, attempts):
        """
        Формує клітинку задачі з переліку спроб команди.

        :param letter: літера задачі
        :param attempts: спроби, впорядковані за часом
        :return: ProblemCell
        """
        cell = ProblemCell(letter=letter)
        for attempt in attempts:
            if attempt.is_accepted:
                cell.solved = True
                elapsed = attempt.submitted_at - self._training.start_at
                cell.solve_minute = int(elapsed.total_seconds() // 60)
                break
            cell.wrong_attempts += 1
        return cell

    def calculate(self):
        """
        Будує таблицю результатів.

        :return: список TeamResult, відсортований за місцем
        """
        lettered = self._training.lettered_problems()
        problems = [problem for _, problem in lettered]
        teams = list(self._training.teams.prefetch_related("members"))
        grouped = self._load_attempts(teams, problems)

        results = []
        for team in teams:
            cells = [self._build_cell(letter, grouped.get((team.pk, problem.pk), [])) for letter, problem in lettered]
            results.append(TeamResult(team=team, cells=cells))

        self._mark_first_solves(results, len(problems))
        results.sort(key=TeamResult.sort_key)
        self._assign_ranks(results)
        return results

    @staticmethod
    def _mark_first_solves(results, problem_count):
        """
        Позначає команди, що першими розв'язали кожну задачу.

        :param results: рядки таблиці
        :param problem_count: кількість задач
        """
        for index in range(problem_count):
            solved_cells = [row.cells[index] for row in results if row.cells[index].solved]
            if not solved_cells:
                continue
            best_minute = min(cell.solve_minute for cell in solved_cells)
            for cell in solved_cells:
                # Команди, що розв'язали задачу на тій самій хвилині, ділять першість
                cell.first_to_solve = cell.solve_minute == best_minute

    @staticmethod
    def _assign_ranks(results):
        """
        Призначає місця; команди з однаковими показниками ділять місце.

        :param results: відсортовані рядки таблиці
        """
        for position, row in enumerate(results, start=1):
            previous = results[position - 2] if position > 1 else None
            same = previous and (previous.solved, previous.penalty) == (row.solved, row.penalty)
            row.rank = previous.rank if same else position
