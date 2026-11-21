from datetime import timedelta

from django.test import TestCase

from training.services import StandingsCalculator, UserStatistics

from .helpers import attempt, make_problem, make_team, make_training, make_user


class StandingsCalculatorTests(TestCase):
    """Модульні тести обчислення таблиці результатів ICPC."""

    def setUp(self):
        self.a1, self.a2, self.b1 = make_user("a1"), make_user("a2"), make_user("b1")
        self.team_a = make_team("A", [self.a1, self.a2])
        self.team_b = make_team("B", [self.b1])
        self.p1 = make_problem("P1", 800)
        self.p2 = make_problem("P2", 1200)
        self.training = make_training([self.p1, self.p2], [self.team_a, self.team_b])
        self.start = self.training.start_at

    def test_penalty_includes_twenty_minutes_per_wrong_attempt(self):
        """ТВ-3.1: штраф = хвилина розв'язання + 20 × невдалі спроби."""
        attempt(self.a1, self.p1, "wrong", self.start + timedelta(minutes=10))
        attempt(self.a2, self.p1, "wrong", self.start + timedelta(minutes=20))
        attempt(self.a1, self.p1, "ok", self.start + timedelta(minutes=30))
        row = next(r for r in StandingsCalculator(self.training).calculate() if r.team == self.team_a)
        self.assertEqual(row.solved, 1)
        self.assertEqual(row.penalty, 30 + 2 * 20)
        self.assertEqual(row.cells[0].label, "+2")

    def test_order_by_solved_then_penalty(self):
        """ТВ-3.2: більше розв'язаних — вище; за рівності — менший штраф."""
        attempt(self.a1, self.p1, "wrong", self.start + timedelta(minutes=5))
        attempt(self.a1, self.p1, "ok", self.start + timedelta(minutes=30))
        attempt(self.b1, self.p1, "ok", self.start + timedelta(minutes=45))
        rows = StandingsCalculator(self.training).calculate()
        self.assertEqual([r.team.name for r in rows], ["B", "A"])
        self.assertEqual([r.rank for r in rows], [1, 2])

    def test_attempts_after_accept_and_outside_window_ignored(self):
        """ТВ-3.3: спроби після зарахування та поза межами тренування не враховуються."""
        attempt(self.b1, self.p1, "wrong", self.start - timedelta(minutes=5))
        attempt(self.b1, self.p1, "ok", self.start + timedelta(minutes=12))
        attempt(self.b1, self.p1, "wrong", self.start + timedelta(minutes=40))
        attempt(self.b1, self.p2, "ok", self.training.end_at + timedelta(minutes=1))
        row = next(r for r in StandingsCalculator(self.training).calculate() if r.team == self.team_b)
        self.assertEqual((row.solved, row.penalty), (1, 12))

    def test_equal_results_share_rank_and_first_solve_marked(self):
        """ТВ-3.4: однакові показники — спільне місце; позначка першого розв'язання."""
        attempt(self.a1, self.p1, "ok", self.start + timedelta(minutes=20))
        attempt(self.b1, self.p2, "ok", self.start + timedelta(minutes=20))
        rows = StandingsCalculator(self.training).calculate()
        self.assertEqual([r.rank for r in rows], [1, 1])
        self.assertTrue(rows[0].cells[0].first_to_solve or rows[1].cells[0].first_to_solve)

    def test_teams_with_same_minute_share_first_solve(self):
        """ТВ-3.6: команди, що розв'язали задачу на одній хвилині, обидві позначаються першими."""
        attempt(self.a1, self.p1, "ok", self.start + timedelta(minutes=20, seconds=5))
        attempt(self.b1, self.p1, "ok", self.start + timedelta(minutes=20, seconds=40))
        rows = StandingsCalculator(self.training).calculate()
        self.assertTrue(all(row.cells[0].first_to_solve for row in rows))

    def test_problems_get_letters_by_difficulty(self):
        """ТВ-3.5: задачам призначаються літери A, B за зростанням складності."""
        self.assertEqual([letter for letter, _ in self.training.lettered_problems()], ["A", "B"])
        self.assertEqual(self.training.lettered_problems()[0][1], self.p1)


class UserStatisticsTests(TestCase):
    """Модульні тести показників прогресу студента."""

    def test_accuracy_score_and_unique_solved(self):
        """ТВ-5.1: точність, бали та унікальні розв'язані задачі."""
        user = make_user("s")
        p1, p2 = make_problem("X", 800), make_problem("Y", 1500)
        start = make_training([p1], []).start_at
        attempt(user, p1, "wrong", start)
        attempt(user, p1, "ok", start)
        attempt(user, p1, "ok", start)
        attempt(user, p2, "ok", start)
        stats = UserStatistics(user)
        self.assertEqual(stats.solved_count, 2)
        self.assertEqual(stats.accuracy, 75)
        self.assertEqual(stats.score, 8 + 15)
        self.assertEqual(dict(stats.by_level())["1200–1599"], 1)

    def test_empty_statistics(self):
        """ТВ-5.2: для нового студента показники дорівнюють нулю без помилок."""
        stats = UserStatistics(make_user("new"))
        self.assertEqual((stats.solved_count, stats.accuracy, stats.score), (0, 0, 0))
