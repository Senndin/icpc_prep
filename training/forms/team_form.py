from django import forms

from accounts.models import User
from training.models import Team

from .bootstrap_mixin import BootstrapFormMixin


class TeamForm(BootstrapFormMixin, forms.ModelForm):
    """Форма створення та редагування команди."""

    class Meta:
        model = Team
        fields = ("name", "university", "coach", "members")
        widgets = {"members": forms.SelectMultiple(attrs={"size": 8})}
        help_texts = {"members": "Оберіть до трьох студентів (Ctrl + клік)."}

    def __init__(self, *args, user=None, **kwargs):
        """
        :param user: поточний користувач; тренер не може призначити іншого тренера
        """
        super().__init__(*args, **kwargs)
        self.fields["coach"].queryset = User.objects.filter(role=User.Role.COACH)
        self.fields["members"].queryset = User.objects.filter(role=User.Role.STUDENT)
        if user is not None and user.is_coach:
            self.fields["coach"].initial = user
            self.fields["coach"].disabled = True

    def clean_members(self):
        """
        Перевіряє склад: не більше трьох студентів, кожен лише в одній команді.

        :return: обрані учасники
        """
        members = self.cleaned_data["members"]
        if len(members) > Team.MAX_MEMBERS:
            raise forms.ValidationError(f"У команді ICPC не може бути більше {Team.MAX_MEMBERS} учасників.")
        busy = [m for m in members if m.teams.exclude(pk=self.instance.pk).exists()]
        if busy:
            names = ", ".join(str(member) for member in busy)
            raise forms.ValidationError(f"Вже перебувають в іншій команді: {names}.")
        return members
