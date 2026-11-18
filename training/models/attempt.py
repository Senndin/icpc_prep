from django.conf import settings
from django.db import models
from django.utils import timezone


class Attempt(models.Model):
    """
    Спроба розв'язання задачі студентом.

    Створюється вручну (позначка студента) або під час
    синхронізації з Codeforces.
    """

    class Verdict(models.TextChoices):
        """Результат спроби."""

        ACCEPTED = "ok", "Зараховано"
        WRONG = "wrong", "Невдала спроба"

    class Source(models.TextChoices):
        """Спосіб надходження спроби."""

        MANUAL = "manual", "Вручну"
        CODEFORCES = "cf", "Codeforces"

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, verbose_name="студент", on_delete=models.CASCADE, related_name="attempts"
    )
    problem = models.ForeignKey(
        "training.Problem", verbose_name="задача", on_delete=models.CASCADE, related_name="attempts"
    )
    verdict = models.CharField("вердикт", max_length=10, choices=Verdict.choices)
    submitted_at = models.DateTimeField("час спроби", default=timezone.now)
    source = models.CharField("джерело", max_length=10, choices=Source.choices, default=Source.MANUAL)
    cf_submission_id = models.BigIntegerField("ID посилки CF", null=True, blank=True, unique=True)

    class Meta:
        verbose_name = "спроба"
        verbose_name_plural = "спроби"
        ordering = ["-submitted_at"]

    def __str__(self):
        """:return: опис спроби"""
        return f"{self.user} — {self.problem} — {self.get_verdict_display()}"

    @property
    def is_accepted(self):
        """:return: True, якщо спробу зараховано"""
        return self.verdict == self.Verdict.ACCEPTED
