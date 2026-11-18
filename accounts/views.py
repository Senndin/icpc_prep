from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.db.models import Q
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.views import View
from django.views.generic import CreateView, ListView, UpdateView

from training.services import CodeforcesClient, CodeforcesError, SubmissionSynchronizer

from .forms import ProfileForm, RegistrationForm, RoleForm
from .mixins import AdminRequiredMixin, QueryStringMixin
from .models import User


class RegisterView(CreateView):
    """Реєстрація студента з автоматичним входом."""

    form_class = RegistrationForm
    template_name = "accounts/register.html"
    success_url = reverse_lazy("training:dashboard")

    def form_valid(self, form):
        """Зберігає користувача, виконує вхід і показує повідомлення."""
        response = super().form_valid(form)
        login(self.request, self.object)
        messages.success(self.request, "Реєстрація успішна. Ласкаво просимо!")
        return response


class ProfileView(LoginRequiredMixin, SuccessMessageMixin, UpdateView):
    """Редагування профілю поточного користувача."""

    form_class = ProfileForm
    template_name = "accounts/profile.html"
    success_url = reverse_lazy("accounts:profile")
    success_message = "Профіль збережено."

    def get_object(self, queryset=None):
        """:return: поточний користувач"""
        return self.request.user


class SyncCodeforcesView(LoginRequiredMixin, View):
    """Синхронізація спроб користувача з Codeforces."""

    def post(self, request):
        """
        Завантажує спроби з Codeforces для поточного користувача.

        :param request: HTTP-запит
        :return: перенаправлення на профіль
        """
        user = request.user
        if not user.codeforces_handle:
            messages.warning(request, "Спочатку вкажіть хендл Codeforces у профілі.")
            return redirect("accounts:profile")
        try:
            created = SubmissionSynchronizer(CodeforcesClient()).sync_user(user)
        except CodeforcesError as error:
            messages.error(request, f"Не вдалося синхронізувати: {error}")
        else:
            messages.success(request, f"Синхронізацію завершено. Нових спроб: {created}.")
        return redirect("accounts:profile")


class UserListView(AdminRequiredMixin, QueryStringMixin, ListView):
    """Перелік користувачів для адміністратора."""

    model = User
    template_name = "accounts/user_list.html"
    paginate_by = 20

    def get_queryset(self):
        """Фільтрує користувачів за роллю та пошуковим рядком."""
        queryset = User.objects.all()
        role = self.request.GET.get("role")
        query = self.request.GET.get("q", "").strip()
        if role:
            queryset = queryset.filter(role=role)
        if query:
            queryset = queryset.filter(Q(username__icontains=query) | Q(last_name__icontains=query))
        return queryset

    def get_context_data(self, **kwargs):
        """Додає перелік ролей до контексту."""
        context = super().get_context_data(**kwargs)
        context["roles"] = User.Role.choices
        return context


class UserRoleUpdateView(AdminRequiredMixin, SuccessMessageMixin, UpdateView):
    """Зміна ролі користувача."""

    model = User
    form_class = RoleForm
    template_name = "accounts/user_role_form.html"
    success_url = reverse_lazy("accounts:users")
    success_message = "Роль користувача %(username)s оновлено."

    def form_valid(self, form):
        """
        Не дозволяє адміністратору позбавити прав або заблокувати самого себе.

        :param form: валідна форма ролі
        :return: HTTP-відповідь
        """
        if self.object.pk == self.request.user.pk:
            messages.warning(self.request, "Не можна змінювати власну роль або блокувати власний обліковий запис.")
            return redirect("accounts:users")
        return super().form_valid(form)

    def get_success_message(self, cleaned_data):
        """:return: текст повідомлення з логіном користувача"""
        return self.success_message % {"username": self.object.username}
