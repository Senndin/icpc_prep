from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.urls import reverse_lazy
from django.utils import timezone
from django.views.generic import CreateView, DeleteView, DetailView, ListView, UpdateView

from accounts.mixins import ManagerRequiredMixin, QueryStringMixin
from training.forms import TrainingForm
from training.models import Training
from training.services import StandingsCalculator, UserStatistics


class OwnTrainingsMixin:
    """Тренер змінює лише власні тренування; адміністратор — будь-які."""

    def get_queryset(self):
        """:return: тренування, доступні для зміни"""
        queryset = Training.objects.all()
        if not self.request.user.is_admin_role:
            queryset = queryset.filter(created_by=self.request.user)
        return queryset


class TrainingListView(LoginRequiredMixin, QueryStringMixin, ListView):
    """Перелік тренувань з фільтром за станом."""

    model = Training
    template_name = "training/training_list.html"
    paginate_by = 10

    def get_queryset(self):
        """Фільтрує тренування за станом: майбутні, поточні, завершені."""
        now = timezone.now()
        queryset = Training.objects.prefetch_related("teams", "problems")
        status = self.request.GET.get("status")
        if status == "upcoming":
            queryset = queryset.filter(start_at__gt=now)
        elif status == "running":
            queryset = queryset.filter(start_at__lte=now, end_at__gte=now)
        elif status == "finished":
            queryset = queryset.filter(end_at__lt=now)
        return queryset

    def get_context_data(self, **kwargs):
        """Додає обраний стан до контексту."""
        context = super().get_context_data(**kwargs)
        context["status"] = self.request.GET.get("status", "")
        return context


class TrainingDetailView(LoginRequiredMixin, DetailView):
    """Сторінка тренування з задачами та таблицею результатів ICPC."""

    model = Training
    template_name = "training/training_detail.html"

    def get_context_data(self, **kwargs):
        """Додає задачі з літерами, таблицю результатів і розв'язані задачі користувача."""
        context = super().get_context_data(**kwargs)
        context["lettered"] = self.object.lettered_problems()
        context["standings"] = StandingsCalculator(self.object).calculate()
        context["solved_ids"] = UserStatistics(self.request.user).solved_ids()
        user = self.request.user
        context["can_edit"] = user.is_admin_role or self.object.created_by_id == user.pk
        return context


class TrainingCreateView(ManagerRequiredMixin, SuccessMessageMixin, CreateView):
    """Створення тренування."""

    model = Training
    form_class = TrainingForm
    template_name = "training/training_form.html"
    success_message = "Тренування «%(title)s» створено."

    def form_valid(self, form):
        """Зберігає автора тренування."""
        form.instance.created_by = self.request.user
        return super().form_valid(form)


class TrainingUpdateView(ManagerRequiredMixin, OwnTrainingsMixin, SuccessMessageMixin, UpdateView):
    """Редагування тренування."""

    model = Training
    form_class = TrainingForm
    template_name = "training/training_form.html"
    success_message = "Зміни в тренуванні «%(title)s» збережено."


class TrainingDeleteView(ManagerRequiredMixin, OwnTrainingsMixin, DeleteView):
    """Видалення тренування."""

    model = Training
    template_name = "training/confirm_delete.html"
    success_url = reverse_lazy("training:training_list")

    def form_valid(self, form):
        """Видаляє тренування та показує повідомлення."""
        messages.success(self.request, f"Тренування «{self.object.title}» видалено.")
        return super().form_valid(form)
