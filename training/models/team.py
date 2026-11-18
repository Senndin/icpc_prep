from django.conf import settings
from django.db import models
from django.urls import reverse


class Team(models.Model):
    """Команда формату ICPC: до трьох студентів і тренер."""

    MAX_MEMBERS = 3

    name = models.CharField("назва", max_length=100, unique=True)
    coach = models.ForeignKey(
        settings.AUTH_USER_MODEL, verbose_name="тренер", null=True, blank=True,
        on_delete=models.SET_NULL, related_name="coached_teams",
        limit_choices_to={"role": "coach"},
    )
    members = models.ManyToManyField(
        settings.AUTH_USER_MODEL, verbose_name="учасники", blank=True, related_name="teams",
        limit_choices_to={"role": "student"},
    )
    university = models.CharField("заклад освіти", max_length=150, blank=True)
    created_at = models.DateTimeField("створено", auto_now_add=True)

    class Meta:
        verbose_name = "команда"
        verbose_name_plural = "команди"
        ordering = ["name"]

    def __str__(self):
        """:return: назва команди"""
        return self.name

    def get_absolute_url(self):
        """:return: адреса сторінки команди"""
        return reverse("training:team_detail", args=[self.pk])

    def is_full(self):
        """
        Перевіряє, чи укомплектовано команду.

        :return: True, якщо учасників MAX_MEMBERS
        """
        return self.members.count() >= self.MAX_MEMBERS
