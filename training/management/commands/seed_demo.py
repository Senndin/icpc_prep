import random
from datetime import timedelta
from pathlib import Path

from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from accounts.models import User
from training.models import Attempt, Problem, Tag, Team, Training
from training.services import ProblemImporter

FIXTURE = Path(__file__).resolve().parents[2] / "fixtures" / "demo_problems.json"

STUDENTS = [
    ("student1", "Олександр", "Бондаренко", "HNEU Bytes"),
    ("student2", "Марія", "Ткаченко", "HNEU Bytes"),
    ("student3", "Іван", "Мельник", "HNEU Bytes"),
    ("student4", "Анна", "Шевченко", "Kharkiv Lambdas"),
    ("student5", "Дмитро", "Кравченко", "Kharkiv Lambdas"),
    ("student6", "Софія", "Олійник", "Kharkiv Lambdas"),
    ("student7", "Максим", "Литвиненко", "Segment Tree Squad"),
    ("student8", "Вікторія", "Савченко", "Segment Tree Squad"),
]


class Command(BaseCommand):
    """Заповнює базу демонстраційними даними для перевірки та захисту."""

    help = "Створює демонстраційних користувачів, команди, задачі, тренування та спроби"

    @transaction.atomic
    def handle(self, *args, **options):
        """Виконує заповнення бази."""
        random.seed(2026)
        Attempt.objects.all().delete()
        Training.objects.all().delete()
        Team.objects.all().delete()
        Problem.objects.all().delete()
        Tag.objects.all().delete()

        admin, _ = User.objects.get_or_create(username="admin", defaults={"first_name": "Адміністратор", "last_name": "Системи"})
        admin.role, admin.is_staff, admin.is_superuser = User.Role.ADMIN, True, True
        admin.set_password("admin12345")
        admin.save()

        coach, _ = User.objects.get_or_create(username="coach", defaults={"first_name": "Ірина", "last_name": "Коваленко"})
        coach.role = User.Role.COACH
        coach.set_password("coach12345")
        coach.save()

        teams = {}
        for username, first, last, team_name in STUDENTS:
            user, _ = User.objects.get_or_create(username=username, defaults={"first_name": first, "last_name": last})
            user.role = User.Role.STUDENT
            user.set_password("student12345")
            user.save()
            team = teams.get(team_name) or Team.objects.create(name=team_name, coach=coach, university="ХНЕУ ім. С. Кузнеця")
            teams[team_name] = team
            team.members.add(user)

        with FIXTURE.open("rb") as stream:
            ProblemImporter(author=coach).import_json(stream)

        now = timezone.now().replace(second=0, microsecond=0)
        by_code = {p.code: p for p in Problem.objects.all()}
        all_teams = list(teams.values())

        first = self._training("Тренування №1: жадібні алгоритми та сортування", now - timedelta(days=14), 300,
                               ["231A", "158B", "489B", "339A", "279B", "4C"], all_teams, coach)
        second = self._training("Тренування №2: динамічне програмування", now - timedelta(minutes=95), 300,
                                ["189A", "433B", "455A", "489C", "474D"], all_teams, coach)
        self._training("Відбір на півфінал ICPC 2026", now + timedelta(days=5), 300,
                       ["1A", "230B", "466C", "580C", "20C", "118A"], all_teams, coach)

        # Сила команд впливає на ймовірність розв'язання
        strength = {"HNEU Bytes": 1.0, "Kharkiv Lambdas": 0.9, "Segment Tree Squad": 0.75}
        self._simulate(first, strength, 300)
        self._simulate(second, strength, 95)

        # Самостійна практика поза тренуваннями
        easy = [p for p in by_code.values() if p.rating and p.rating <= 1300]
        for user in User.objects.filter(role=User.Role.STUDENT):
            for problem in random.sample(easy, random.randint(5, 12)):
                moment = now - timedelta(days=random.randint(20, 60), minutes=random.randint(0, 600))
                for _ in range(random.choice([0, 0, 0, 1, 2])):
                    Attempt.objects.create(user=user, problem=problem, verdict="wrong", submitted_at=moment)
                    moment += timedelta(minutes=7)
                Attempt.objects.create(user=user, problem=problem, verdict="ok", submitted_at=moment)

        self.stdout.write(self.style.SUCCESS(
            "Демо-дані створено. Логіни: admin/admin12345, coach/coach12345, student1..student8/student12345"
        ))

    @staticmethod
    def _training(title, start, minutes, codes, teams, coach):
        """
        Створює тренування.

        :return: тренування
        """
        training = Training.objects.create(
            title=title, start_at=start, end_at=start + timedelta(minutes=minutes), created_by=coach,
            description="Тренування у форматі ICPC: 5 годин, штраф 20 хвилин за кожну невдалу спробу.",
        )
        training.problems.set([problem for problem in Problem.objects.all() if problem.code in codes])
        training.teams.set(teams)
        return training

    @staticmethod
    def _simulate(training, strength, elapsed):
        """
        Генерує спроби команд у межах тренування.

        :param training: тренування
        :param strength: словник сили команд
        :param elapsed: скільки хвилин тренування минуло
        """
        for team in training.teams.all():
            members = list(team.members.all())
            for index, (_, problem) in enumerate(training.lettered_problems()):
                chance = strength[team.name] - index * 0.1
                minute = random.randint(8, 40) + index * random.randint(15, 35)
                for _ in range(random.choice([0, 0, 0, 1, 1, 2])):
                    if minute >= elapsed:
                        break
                    Attempt.objects.create(user=random.choice(members), problem=problem, verdict="wrong",
                                           submitted_at=training.start_at + timedelta(minutes=minute))
                    minute += random.randint(5, 20)
                if random.random() < chance and minute < elapsed:
                    Attempt.objects.create(user=random.choice(members), problem=problem, verdict="ok",
                                           submitted_at=training.start_at + timedelta(minutes=minute))
