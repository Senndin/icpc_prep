from django import forms

from training.models import Problem

from .bootstrap_mixin import BootstrapFormMixin


class ProblemForm(BootstrapFormMixin, forms.ModelForm):
    """Форма додавання та редагування задачі."""

    class Meta:
        model = Problem
        fields = ("title", "cf_contest_id", "cf_index", "rating", "tags", "url", "statement")
        widgets = {
            "tags": forms.SelectMultiple(attrs={"size": 8}),
            "statement": forms.Textarea(attrs={"rows": 4}),
        }

    def clean(self):
        """
        Перевіряє узгодженість полів Codeforces.

        :return: очищені дані
        """
        data = super().clean()
        contest_id, index = data.get("cf_contest_id"), data.get("cf_index", "").strip()
        if bool(contest_id) != bool(index):
            raise forms.ValidationError("Для задачі Codeforces вкажіть і ID контесту, і індекс (наприклад 4 і A).")
        data["cf_index"] = index.upper()
        if contest_id:
            duplicate = Problem.objects.filter(cf_contest_id=contest_id, cf_index=data["cf_index"])
            if duplicate.exclude(pk=self.instance.pk).exists():
                raise forms.ValidationError("Задача з таким кодом Codeforces уже є в банку.")
        return data

    def save(self, commit=True):
        """
        Визначає джерело задачі перед збереженням.

        :param commit: чи зберігати до бази
        :return: задача
        """
        problem = super().save(commit=False)
        problem.source = Problem.Source.CODEFORCES if problem.cf_contest_id else Problem.Source.MANUAL
        if commit:
            problem.save()
            self.save_m2m()
        return problem
