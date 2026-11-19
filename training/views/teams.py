from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.urls import reverse_lazy
from django.views.generic import CreateView, DeleteView, DetailView, ListView, UpdateView

from accounts.mixins import ManagerRequiredMixin
from training.forms import TeamForm
from training.models import Team
from training.services import UserStatistics


class CoachTeamsMixin:
    """Обмежує тренера лише його командами; адміністратор бачить усі."""

    def get_queryset(self):
        """:return: команди, доступні для зміни поточним користувачем"""
        queryset = Team.objects.all()
        if not self.request.user.is_admin_role:
            queryset = queryset.filter(coach=self.request.user)
        return queryset


class TeamListView(LoginRequiredMixin, ListView):
    """Перелік команд."""

    model = Team
    template_name = "training/team_list.html"

    def get_queryset(self):
        """:return: команди з тренерами та учасниками"""
        return Team.objects.select_related("coach").prefetch_related("members")


class TeamDetailView(LoginRequiredMixin, DetailView):
    """Сторінка команди зі статистикою учасників."""

    model = Team
    template_name = "training/team_detail.html"

    def get_context_data(self, **kwargs):
        """Додає статистику кожного учасника та тренування команди."""
        context = super().get_context_data(**kwargs)
        context["member_stats"] = [(member, UserStatistics(member)) for member in self.object.members.all()]
        context["trainings"] = self.object.trainings.all()[:10]
        user = self.request.user
        context["can_edit"] = user.is_admin_role or self.object.coach_id == user.pk
        return context


class TeamCreateView(ManagerRequiredMixin, SuccessMessageMixin, CreateView):
    """Створення команди."""

    model = Team
    form_class = TeamForm
    template_name = "training/team_form.html"
    success_message = "Команду «%(name)s» створено."

    def get_form_kwargs(self):
        """Передає поточного користувача у форму."""
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        return kwargs

    def form_valid(self, form):
        """Тренер автоматично стає тренером створеної команди."""
        if self.request.user.is_coach:
            form.instance.coach = self.request.user
        return super().form_valid(form)


class TeamUpdateView(ManagerRequiredMixin, CoachTeamsMixin, SuccessMessageMixin, UpdateView):
    """Редагування команди."""

    model = Team
    form_class = TeamForm
    template_name = "training/team_form.html"
    success_message = "Зміни в команді «%(name)s» збережено."

    def get_form_kwargs(self):
        """Передає поточного користувача у форму."""
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        return kwargs


class TeamDeleteView(ManagerRequiredMixin, CoachTeamsMixin, DeleteView):
    """Видалення команди."""

    model = Team
    template_name = "training/confirm_delete.html"
    success_url = reverse_lazy("training:team_list")

    def form_valid(self, form):
        """Видаляє команду та показує повідомлення."""
        messages.success(self.request, f"Команду «{self.object.name}» видалено.")
        return super().form_valid(form)
