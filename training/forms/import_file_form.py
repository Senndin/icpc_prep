from django import forms

from .bootstrap_mixin import BootstrapFormMixin


class ImportFileForm(BootstrapFormMixin, forms.Form):
    """Форма завантаження файлу задач у форматі JSON або CSV."""

    MAX_SIZE = 1024 * 1024
    file = forms.FileField(label="Файл задач (.json або .csv)")

    def clean_file(self):
        """
        Перевіряє розширення та розмір файлу.

        :return: завантажений файл
        """
        uploaded = self.cleaned_data["file"]
        if not uploaded.name.lower().endswith((".json", ".csv")):
            raise forms.ValidationError("Підтримуються лише файли .json та .csv.")
        if uploaded.size > self.MAX_SIZE:
            raise forms.ValidationError("Розмір файлу не може перевищувати 1 МБ.")
        return uploaded
