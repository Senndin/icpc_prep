from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.urls import reverse


class Problem(models.Model):
    """
    Олімпіадна задача в банку задач.

    Задача може бути імпортована з Codeforces або додана вручну тренером.
    """

    class Source(models.TextChoices):
        """Джерело походження задачі."""

        CODEFORCES = "cf", "Codeforces"
        MANUAL = "manual", "Власна"

    title = models.CharField("назва", max_length=200)
    source = models.CharField("джерело", max_length=10, choices=Source.choices, default=Source.MANUAL)
    cf_contest_id = models.PositiveIntegerField("ID контесту CF", null=True, blank=True)
    cf_index = models.CharField("індекс задачі CF", max_length=5, blank=True)
    rating = models.PositiveIntegerField(
        "складність",
        null=True,
        blank=True,
        validators=[MinValueValidator(800), MaxValueValidator(3500)],
        help_text="Рейтинг складності за шкалою Codeforces (800–3500).",
    )
    tags = models.ManyToManyField("training.Tag", verbose_name="теги", blank=True, related_name="problems")
    url = models.URLField("посилання", blank=True)
    statement = models.TextField("короткий опис", blank=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, verbose_name="автор запису", null=True, blank=True,
        on_delete=models.SET_NULL, related_name="created_problems",
    )
    created_at = models.DateTimeField("створено", auto_now_add=True)

    class Meta:
        verbose_name = "задача"
        verbose_name_plural = "задачі"
        ordering = ["rating", "title"]
        constraints = [
            models.UniqueConstraint(
                fields=["cf_contest_id", "cf_index"],
                condition=models.Q(source="cf"),
                name="unique_codeforces_problem",
            )
        ]

    def __str__(self):
        """:return: код і назва задачі"""
        return f"{self.code} {self.title}" if self.code else self.title

    @property
    def code(self):
        """
        Повертає код задачі на Codeforces.

        :return: рядок на кшталт «4A» або порожній рядок
        """
        if self.cf_contest_id and self.cf_index:
            return f"{self.cf_contest_id}{self.cf_index}"
        return ""

    def get_external_url(self):
        """
        Формує посилання на умову задачі.

        :return: URL умови або порожній рядок
        """
        if self.url:
            return self.url
        if self.code:
            return f"https://codeforces.com/problemset/problem/{self.cf_contest_id}/{self.cf_index}"
        return ""

    def get_absolute_url(self):
        """:return: адреса сторінки задачі"""
        return reverse("training:problem_detail", args=[self.pk])

    def difficulty_level(self):
        """
        Визначає рівень складності за рейтингом.

        :return: «легка», «середня», «складна» або «—»
        """
        if self.rating is None:
            return "—"
        if self.rating < 1200:
            return "легка"
        if self.rating < 1800:
            return "середня"
        return "складна"
