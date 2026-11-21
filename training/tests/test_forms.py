from django.test import TestCase

from accounts.forms import ProfileForm
from accounts.models import User
from training.forms import ProblemForm, TeamForm, TrainingForm

from .helpers import make_problem, make_team, make_user


class FormValidationTests(TestCase):
    """Тести перевірки допустимості даних, що вводить користувач."""

    def test_team_cannot_have_more_than_three_members(self):
        """ТВ-1.1: команда не може мати більше трьох учасників."""
        students = [make_user(f"s{i}") for i in range(4)]
        form = TeamForm(data={"name": "Big", "members": [s.pk for s in students]})
        self.assertFalse(form.is_valid())
        self.assertIn("members", form.errors)

    def test_student_cannot_be_in_two_teams(self):
        """ТВ-1.2: студент не може бути учасником двох команд."""
        student = make_user("busy")
        make_team("First", [student])
        form = TeamForm(data={"name": "Second", "members": [student.pk]})
        self.assertFalse(form.is_valid())

    def test_only_students_can_be_members(self):
        """ТВ-1.3: учасником команди може бути лише студент."""
        coach = make_user("coach", role=User.Role.COACH)
        form = TeamForm(data={"name": "T", "members": [coach.pk]})
        self.assertFalse(form.is_valid())

    def test_training_end_must_be_after_start(self):
        """ТВ-1.4: завершення тренування має бути пізніше за початок."""
        problem = make_problem("P")
        form = TrainingForm(data={"title": "T", "start_at": "2026-11-10T10:00", "end_at": "2026-11-10T09:00",
                                  "problems": [problem.pk]})
        self.assertFalse(form.is_valid())
        self.assertIn("пізніше", str(form.errors))

    def test_problem_requires_both_codeforces_fields(self):
        """ТВ-1.5: для задачі Codeforces потрібні і ID контесту, і індекс."""
        form = ProblemForm(data={"title": "X", "cf_contest_id": 4, "cf_index": ""})
        self.assertFalse(form.is_valid())

    def test_problem_rating_range(self):
        """ТВ-1.6: складність задачі має бути в межах 800–3500."""
        form = ProblemForm(data={"title": "X", "rating": 100})
        self.assertFalse(form.is_valid())
        self.assertIn("rating", form.errors)

    def test_valid_problem_form_sets_source(self):
        """ТВ-1.7: коректна задача Codeforces зберігається з джерелом «cf»."""
        form = ProblemForm(data={"title": "Watermelon", "cf_contest_id": 4, "cf_index": "a", "rating": 800})
        self.assertTrue(form.is_valid())
        self.assertEqual((form.save().source, form.instance.cf_index), ("cf", "A"))

    def test_codeforces_handle_must_be_unique(self):
        """ТВ-1.8: один хендл Codeforces не можуть вказати два користувачі."""
        make_user("first", codeforces_handle="Tourist")
        second = make_user("second")
        form = ProfileForm(data={"first_name": "А", "last_name": "Б", "codeforces_handle": "tourist"}, instance=second)
        self.assertFalse(form.is_valid())
        self.assertIn("codeforces_handle", form.errors)
