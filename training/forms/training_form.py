from django import forms

from training.models import Training

from .bootstrap_mixin import BootstrapFormMixin


class TrainingForm(BootstrapFormMixin, forms.ModelForm):
    """Форма створення та редагування тренування."""

    MAX_PROBLEMS = 26

    class Meta:
        model = Training
        fields = ("title", "description", "start_at", "end_at", "problems", "teams")
        widgets = {
            "description": forms.Textarea(attrs={"rows": 3}),
            "start_at": forms.DateTimeInput(attrs={"type": "datetime-local"}, format="%Y-%m-%dT%H:%M"),
            "end_at": forms.DateTimeInput(attrs={"type": "datetime-local"}, format="%Y-%m-%dT%H:%M"),
            "problems": forms.SelectMultiple(attrs={"size": 10}),
            "teams": forms.SelectMultiple(attrs={"size": 5}),
        }

    def clean(self):
        """
        Перевіряє часові межі та кількість задач.

        :return: очищені дані
        """
        data = super().clean()
        start, end = data.get("start_at"), data.get("end_at")
        if start and end and end <= start:
            raise forms.ValidationError("Час завершення має бути пізніше за час початку.")
        problems = data.get("problems")
        if problems is not None and len(problems) > self.MAX_PROBLEMS:
            raise forms.ValidationError(f"Тренування може містити не більше {self.MAX_PROBLEMS} задач (A–Z).")
        return data
