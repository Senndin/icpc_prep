from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.db.models import Count, Q
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.utils.http import url_has_allowed_host_and_scheme
from django.views import View
from django.views.generic import CreateView, DeleteView, DetailView, ListView, UpdateView

from accounts.mixins import ManagerRequiredMixin, QueryStringMixin
from training.forms import ProblemFilterForm, ProblemForm
from training.models import Attempt, Problem
from training.services import UserStatistics


class ProblemListView(LoginRequiredMixin, QueryStringMixin, ListView):
    """Банк задач з пошуком і фільтрами."""

    model = Problem
    template_name = "training/problem_list.html"
    paginate_by = 15

    def get_queryset(self):
        """Застосовує фільтри форми до переліку задач."""
        self.filter_form = ProblemFilterForm(self.request.GET or None)
        self.solved_ids = UserStatistics(self.request.user).solved_ids()
        queryset = Problem.objects.prefetch_related("tags").annotate(
            solved_by=Count("attempts__user", filter=Q(attempts__verdict="ok"), distinct=True)
        )
        if self.filter_form.is_valid():
            data = self.filter_form.cleaned_data
            if data["q"]:
                queryset = queryset.filter(title__icontains=data["q"])
            if data["tag"]:
                queryset = queryset.filter(tags=data["tag"])
            if data["min_rating"]:
                queryset = queryset.filter(rating__gte=data["min_rating"])
            if data["max_rating"]:
                queryset = queryset.filter(rating__lte=data["max_rating"])
            if data["status"] == "solved":
                queryset = queryset.filter(pk__in=self.solved_ids)
            elif data["status"] == "unsolved":
                queryset = queryset.exclude(pk__in=self.solved_ids)
        # Після annotate типове впорядкування моделі не застосовується, тому задаємо його явно:
        # без цього пагінація могла б повторювати або пропускати задачі
        return queryset.order_by("rating", "title", "pk")

    def get_context_data(self, **kwargs):
        """Додає форму фільтра, розв'язані задачі та рядок параметрів для пагінації."""
        context = super().get_context_data(**kwargs)
        context["filter_form"] = self.filter_form
        context["solved_ids"] = self.solved_ids
        return context


class ProblemDetailView(LoginRequiredMixin, DetailView):
    """Сторінка задачі зі спробами поточного користувача."""

    model = Problem
    template_name = "training/problem_detail.html"

    def get_context_data(self, **kwargs):
        """Додає спроби, ознаку розв'язання та тренування з цією задачею."""
        context = super().get_context_data(**kwargs)
        attempts = self.object.attempts.filter(user=self.request.user)
        context["my_attempts"] = attempts
        context["is_solved"] = attempts.filter(verdict=Attempt.Verdict.ACCEPTED).exists()
        context["solved_by"] = self.object.attempts.filter(verdict="ok").values("user").distinct().count()
        context["trainings"] = self.object.trainings.all()[:5]
        return context


class ProblemCreateView(ManagerRequiredMixin, SuccessMessageMixin, CreateView):
    """Додавання задачі до банку."""

    model = Problem
    form_class = ProblemForm
    template_name = "training/problem_form.html"
    success_message = "Задачу «%(title)s» додано."

    def form_valid(self, form):
        """Зберігає автора запису."""
        form.instance.created_by = self.request.user
        return super().form_valid(form)


class ProblemUpdateView(ManagerRequiredMixin, SuccessMessageMixin, UpdateView):
    """Редагування задачі."""

    model = Problem
    form_class = ProblemForm
    template_name = "training/problem_form.html"
    success_message = "Зміни в задачі «%(title)s» збережено."


class ProblemDeleteView(ManagerRequiredMixin, DeleteView):
    """Видалення задачі з підтвердженням."""

    model = Problem
    template_name = "training/confirm_delete.html"
    success_url = reverse_lazy("training:problem_list")

    def form_valid(self, form):
        """
        Видаляє задачу, якщо вона не входить до тренувань.

        Видалення задачі з тренування змінило б його таблицю результатів,
        тому така задача захищена від видалення.
        """
        if self.object.trainings.exists():
            messages.error(self.request, f"Задачу «{self.object.title}» не можна видалити: вона входить до тренувань.")
            return redirect(self.object.get_absolute_url())
        messages.success(self.request, f"Задачу «{self.object.title}» видалено.")
        return super().form_valid(form)


class AttemptCreateView(LoginRequiredMixin, View):
    """Реєстрація спроби студента: зараховано або невдала спроба."""

    def post(self, request, pk):
        """
        Створює спробу для задачі.

        :param request: HTTP-запит з полем verdict
        :param pk: id задачі
        :return: перенаправлення на попередню сторінку
        """
        problem = get_object_or_404(Problem, pk=pk)
        verdict = request.POST.get("verdict")
        if not request.user.is_student:
            messages.warning(request, "Позначати спроби можуть лише студенти.")
        elif verdict not in Attempt.Verdict.values:
            messages.error(request, "Невідомий вердикт.")
        elif Attempt.objects.filter(user=request.user, problem=problem, verdict=Attempt.Verdict.ACCEPTED).exists():
            messages.info(request, "Цю задачу вже зараховано, нові спроби не потрібні.")
        else:
            Attempt.objects.create(user=request.user, problem=problem, verdict=verdict)
            if verdict == Attempt.Verdict.ACCEPTED:
                messages.success(request, f"Задачу «{problem.title}» зараховано. Так тримати!")
            else:
                messages.info(request, "Невдалу спробу записано. Вона додасть 20 хв штрафу на тренуванні.")
        return redirect(self._safe_next_url(request, problem))

    @staticmethod
    def _safe_next_url(request, problem):
        """
        Повертає адресу для перенаправлення, дозволяючи лише адреси цього сайту.

        :param request: HTTP-запит з необов'язковим полем next
        :param problem: задача, на сторінку якої повертаємось за замовчуванням
        :return: безпечна адреса
        """
        next_url = request.POST.get("next", "")
        if next_url and url_has_allowed_host_and_scheme(next_url, allowed_hosts={request.get_host()}):
            return next_url
        return problem.get_absolute_url()
