from django import forms

from accounts.models import User


class UniqueHandleMixin:
    """Перевіряє, що хендл Codeforces не використовується іншим користувачем."""

    def clean_codeforces_handle(self):
        """
        Перевіряє унікальність хендла без урахування регістру.

        :return: очищений хендл
        :raises forms.ValidationError: якщо хендл уже зайнятий
        """
        handle = self.cleaned_data.get("codeforces_handle", "").strip()
        if handle:
            taken = User.objects.filter(codeforces_handle__iexact=handle).exclude(pk=self.instance.pk)
            if taken.exists():
                raise forms.ValidationError("Цей хендл Codeforces уже вказав інший користувач.")
        return handle
