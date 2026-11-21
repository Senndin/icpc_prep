import time

from django.test import TestCase
from django.urls import reverse

from training.models import Problem

from .helpers import make_user


class PerformanceTests(TestCase):
    """Перевірка нефункціональної вимоги до часу відгуку."""

    def test_problem_list_responds_within_one_second(self):
        """ТВ-7.1: сторінка банку з 1000 задач формується менш ніж за 1 секунду."""
        Problem.objects.bulk_create(Problem(title=f"Задача {number}", rating=800 + number % 27 * 100)
                                    for number in range(1000))
        make_user("student")
        self.client.login(username="student", password="pass12345")
        started = time.perf_counter()
        response = self.client.get(reverse("training:problem_list"))
        elapsed = time.perf_counter() - started
        self.assertEqual(response.status_code, 200)
        self.assertLess(elapsed, 1.0)
