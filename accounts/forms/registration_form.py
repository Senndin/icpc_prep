from django import forms
from django.contrib.auth.forms import UserCreationForm

from accounts.models import User
from training.forms.bootstrap_mixin import BootstrapFormMixin

from .unique_handle_mixin import UniqueHandleMixin


class RegistrationForm(UniqueHandleMixin, BootstrapFormMixin, UserCreationForm):
    """Форма реєстрації нового студента."""

    first_name = forms.CharField(label="Ім'я", max_length=150)
    last_name = forms.CharField(label="Прізвище", max_length=150)
    email = forms.EmailField(label="Email", required=False)

    class Meta:
        model = User
        fields = ("username", "first_name", "last_name", "email", "codeforces_handle")

    def save(self, commit=True):
        """
        Зберігає користувача з роллю «студент».

        :param commit: чи зберігати одразу до бази
        :return: створений користувач
        """
        user = super().save(commit=False)
        user.role = User.Role.STUDENT
        if commit:
            user.save()
        return user
