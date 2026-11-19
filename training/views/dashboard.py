from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Count, Q
from django.utils import timezone
from django.views.generic import TemplateView

from accounts.models import User
from training.models import Attempt, Problem, Team, Training
from training.services import UserStatistics


class DashboardView(LoginRequiredMixin, TemplateView):
    """Головна сторінка з даними відповідно до ролі користувача."""

    template_name = "training/dashboard.html"

    def get_context_data(self, **kwargs):
        """Формує контекст головної сторінки."""
        context = super().get_context_data(**kwargs)
        user = self.request.user
        now = timezone.now()
        context["counts"] = {
            "problems": Problem.objects.count(),
            "teams": Team.objects.count(),
            "trainings": Training.objects.count(),
            "students": User.objects.filter(role=User.Role.STUDENT).count(),
        }
        trainings = Training.objects.filter(end_at__gte=now).order_by("start_at")
        if user.is_student:
            stats = UserStatistics(user)
            context["stats"] = stats
            context["team"] = user.team
            trainings = trainings.filter(teams__members=user)
            context["recommended"] = self._recommend(stats)
            context["recent_attempts"] = Attempt.objects.filter(user=user).select_related("problem")[:6]
        else:
            teams = Team.objects.prefetch_related("members")
            if user.is_coach:
                teams = teams.filter(coach=user)
            context["my_teams"] = teams.annotate(
                solved=Count("members__attempts__problem", filter=Q(members__attempts__verdict="ok"), distinct=True)
            ).order_by("name")
            context["recent_attempts"] = Attempt.objects.select_related("problem", "user")[:8]
        context["upcoming_trainings"] = trainings.distinct()[:5]
        return context

    @staticmethod
    def _recommend(stats, count=5):
        """
        Підбирає нерозв'язані задачі трохи складніші за поточний рівень.

        :param stats: статистика студента
        :param count: кількість рекомендацій
        :return: набір задач
        """
        solved = Problem.objects.filter(pk__in=stats.solved_ids())
        ratings = [problem.rating for problem in solved if problem.rating]
        level = max(800, round(sum(ratings) / len(ratings) / 100) * 100) if ratings else 800
        return (
            Problem.objects.exclude(pk__in=stats.solved_ids())
            .filter(rating__gte=level, rating__lte=level + 300)
            .prefetch_related("tags")
            .order_by("rating", "pk")[:count]
        )
