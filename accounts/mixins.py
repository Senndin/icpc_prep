from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin


class ManagerRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    """Дозволяє доступ лише тренерам та адміністраторам."""

    def test_func(self):
        """
        Перевіряє роль поточного користувача.

        :return: True, якщо користувач може керувати даними
        """
        return self.request.user.can_manage


class AdminRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    """Дозволяє доступ лише адміністраторам."""

    def test_func(self):
        """:return: True, якщо користувач — адміністратор"""
        return self.request.user.is_admin_role


class QueryStringMixin:
    """Зберігає параметри фільтрації під час переходу між сторінками списку."""

    def get_context_data(self, **kwargs):
        """
        Додає до контексту рядок GET-параметрів без номера сторінки.

        :return: контекст шаблону
        """
        context = super().get_context_data(**kwargs)
        params = self.request.GET.copy()
        params.pop("page", None)
        context["query_string"] = params.urlencode()
        return context
