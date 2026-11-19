from django import forms

from .bootstrap_mixin import BootstrapFormMixin


class CodeforcesImportForm(BootstrapFormMixin, forms.Form):
    """Форма завантаження задач з архіву Codeforces."""

    tags = forms.CharField(
        label="Теги через кому", required=False, help_text="Наприклад: greedy, dp. Порожньо — усі теги."
    )
    min_rating = forms.IntegerField(label="Мінімальна складність", initial=800, min_value=800, max_value=3500)
    max_rating = forms.IntegerField(label="Максимальна складність", initial=1400, min_value=800, max_value=3500)
    limit = forms.IntegerField(label="Кількість задач", initial=20, min_value=1, max_value=200)

    def clean(self):
        """
        Перевіряє, що мінімальна складність не перевищує максимальну.

        :return: очищені дані
        """
        data = super().clean()
        if data.get("min_rating") and data.get("max_rating") and data["min_rating"] > data["max_rating"]:
            raise forms.ValidationError("Мінімальна складність більша за максимальну.")
        data["tag_list"] = [tag.strip() for tag in data.get("tags", "").split(",") if tag.strip()]
        return data
