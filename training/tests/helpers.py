from datetime import timedelta

from django.utils import timezone

from accounts.models import User
from training.models import Attempt, Problem, Team, Training


def make_user(username, role=User.Role.STUDENT, **extra):
    """Створює користувача з паролем pass12345."""
    user = User.objects.create_user(username=username, password="pass12345", role=role, **extra)
    return user


def make_problem(title, rating=800, contest=None, index=""):
    """Створює задачу."""
    source = Problem.Source.CODEFORCES if contest else Problem.Source.MANUAL
    return Problem.objects.create(title=title, rating=rating, cf_contest_id=contest, cf_index=index, source=source)


def make_training(problems, teams, start=None, minutes=300):
    """Створює тренування з задачами та командами."""
    start = start or timezone.now() - timedelta(hours=6)
    training = Training.objects.create(title="Тест", start_at=start, end_at=start + timedelta(minutes=minutes))
    training.problems.set(problems)
    training.teams.set(teams)
    return training


def make_team(name, members):
    """Створює команду з учасниками."""
    team = Team.objects.create(name=name)
    team.members.set(members)
    return team


def attempt(user, problem, verdict, at):
    """Створює спробу в заданий момент."""
    return Attempt.objects.create(user=user, problem=problem, verdict=verdict, submitted_at=at)
