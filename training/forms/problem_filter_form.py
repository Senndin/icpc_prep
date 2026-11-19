from django import forms

from training.models import Tag

from .bootstrap_mixin import BootstrapFormMixin


class ProblemFilterForm(BootstrapFormMixin, forms.Form):
    """Форма пошуку та фільтрації банку задач."""

    STATUS_CHOICES = (("", "Усі задачі"), ("solved", "Розв'язані мною"), ("unsolved", "Нерозв'язані"))

    q = forms.CharField(label="Пошук", required=False)
    tag = forms.ModelChoiceField(label="Тег", queryset=Tag.objects.all(), required=False, empty_label="Усі теги")
    min_rating = forms.IntegerField(label="Від", required=False, min_value=800, max_value=3500)
    max_rating = forms.IntegerField(label="До", required=False, min_value=800, max_value=3500)
    status = forms.ChoiceField(label="Стан", choices=STATUS_CHOICES, required=False)
