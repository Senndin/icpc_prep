from django.test import TestCase
from django.urls import reverse

from accounts.models import User
from training.models import Attempt, Problem

from .helpers import make_problem, make_training, make_user


class AccessAndViewsTests(TestCase):
    """Інтеграційні тести представлень і розмежування доступу."""

    def setUp(self):
        self.student = make_user("student")
        self.coach = make_user("coach", role=User.Role.COACH)
        self.problem = make_problem("Watermelon", 800, 4, "A")

    def test_anonymous_redirected_to_login(self):
        """ТВ-6.1: неавторизованого користувача перенаправлено на сторінку входу."""
        response = self.client.get(reverse("training:problem_list"))
        self.assertRedirects(response, reverse("accounts:login") + "?next=/problems/")

    def test_student_cannot_create_problem(self):
        """ТВ-6.2: студент не має доступу до створення задач (403)."""
        self.client.login(username="student", password="pass12345")
        self.assertEqual(self.client.get(reverse("training:problem_create")).status_code, 403)

    def test_coach_creates_problem(self):
        """ТВ-6.3: тренер додає задачу; її видно в банку."""
        self.client.login(username="coach", password="pass12345")
        response = self.client.post(reverse("training:problem_create"), {"title": "Нова задача", "rating": 1000}, follow=True)
        self.assertContains(response, "Нова задача")
        self.assertEqual(Problem.objects.get(title="Нова задача").created_by, self.coach)

    def test_student_marks_attempt(self):
        """ТВ-6.4: студент позначає задачу як розв'язану."""
        self.client.login(username="student", password="pass12345")
        response = self.client.post(reverse("training:attempt_create", args=[self.problem.pk]), {"verdict": "ok"}, follow=True)
        self.assertContains(response, "зараховано")
        self.assertTrue(Attempt.objects.filter(user=self.student, verdict="ok").exists())

    def test_coach_cannot_mark_attempt(self):
        """ТВ-6.5: тренер не може створювати спроби."""
        self.client.login(username="coach", password="pass12345")
        self.client.post(reverse("training:attempt_create", args=[self.problem.pk]), {"verdict": "ok"})
        self.assertFalse(Attempt.objects.exists())

    def test_problem_filter_by_rating(self):
        """ТВ-6.6: фільтр за складністю повертає лише відповідні задачі."""
        make_problem("Hard", 2000)
        self.client.login(username="student", password="pass12345")
        response = self.client.get(reverse("training:problem_list"), {"min_rating": 1500})
        self.assertContains(response, "Hard")
        self.assertNotContains(response, "Watermelon")

    def test_export_returns_file(self):
        """ТВ-6.7: експорт повертає файл для завантаження."""
        self.client.login(username="coach", password="pass12345")
        response = self.client.get(reverse("training:problem_export"), {"format": "csv"})
        self.assertIn("attachment", response["Content-Disposition"])
        self.assertIn("Watermelon", response.content.decode())

    def test_delete_problem(self):
        """ТВ-6.8: тренер видаляє задачу після підтвердження."""
        self.client.login(username="coach", password="pass12345")
        self.client.post(reverse("training:problem_delete", args=[self.problem.pk]))
        self.assertFalse(Problem.objects.exists())

    def test_registration_creates_student(self):
        """ТВ-6.9: реєстрація створює користувача з роллю «студент»."""
        self.client.post(reverse("accounts:register"), {
            "username": "newbie", "first_name": "Нов", "last_name": "Ачок",
            "password1": "StrongPass2026", "password2": "StrongPass2026",
        })
        self.assertEqual(User.objects.get(username="newbie").role, User.Role.STUDENT)

    def test_external_redirect_is_ignored(self):
        """ТВ-6.10: параметр next із зовнішньою адресою ігнорується (захист від відкритого перенаправлення)."""
        self.client.login(username="student", password="pass12345")
        response = self.client.post(reverse("training:attempt_create", args=[self.problem.pk]),
                                    {"verdict": "wrong", "next": "https://evil.example/"})
        self.assertRedirects(response, self.problem.get_absolute_url())

    def test_solved_problem_is_not_marked_twice(self):
        """ТВ-6.11: розв'язану задачу не можна зарахувати повторно."""
        self.client.login(username="student", password="pass12345")
        url = reverse("training:attempt_create", args=[self.problem.pk])
        self.client.post(url, {"verdict": "ok"})
        self.client.post(url, {"verdict": "ok"})
        self.client.post(url, {"verdict": "wrong"})
        self.assertEqual(Attempt.objects.count(), 1)

    def test_problem_used_in_training_is_protected(self):
        """ТВ-6.12: задачу, що входить до тренування, видалити не можна."""
        make_training([self.problem], [])
        self.client.login(username="coach", password="pass12345")
        response = self.client.post(reverse("training:problem_delete", args=[self.problem.pk]), follow=True)
        self.assertContains(response, "не можна видалити")
        self.assertTrue(Problem.objects.filter(pk=self.problem.pk).exists())

    def test_admin_cannot_change_own_role(self):
        """ТВ-6.13: адміністратор не може змінити власну роль або заблокувати себе."""
        admin = make_user("boss", role=User.Role.ADMIN)
        self.client.login(username="boss", password="pass12345")
        self.client.post(reverse("accounts:user_role", args=[admin.pk]), {"role": "student", "is_active": ""})
        admin.refresh_from_db()
        self.assertEqual((admin.role, admin.is_active), (User.Role.ADMIN, True))

    def test_pagination_keeps_filters(self):
        """ТВ-6.14: посилання на наступну сторінку зберігає параметри фільтра."""
        for number in range(20):
            make_problem(f"Задача {number}", 1000)
        self.client.login(username="student", password="pass12345")
        response = self.client.get(reverse("training:problem_list"), {"min_rating": 900})
        self.assertContains(response, "page=2&min_rating=900")
