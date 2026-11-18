from django import forms

from accounts.models import User
from training.forms.bootstrap_mixin import BootstrapFormMixin

from .unique_handle_mixin import UniqueHandleMixin


class ProfileForm(UniqueHandleMixin, BootstrapFormMixin, forms.ModelForm):
    """Форма редагування власного профілю."""

    class Meta:
        model = User
        fields = ("first_name", "last_name", "email", "codeforces_handle")
        help_texts = {"codeforces_handle": "Потрібен для синхронізації розв'язків з Codeforces."}
