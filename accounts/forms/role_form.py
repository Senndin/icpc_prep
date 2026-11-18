from django import forms

from accounts.models import User
from training.forms.bootstrap_mixin import BootstrapFormMixin


class RoleForm(BootstrapFormMixin, forms.ModelForm):
    """Форма зміни ролі користувача адміністратором."""

    class Meta:
        model = User
        fields = ("role", "is_active")
