from django.conf import settings
from django.db import models
from django.urls import reverse
from django.utils import timezone


class Training(models.Model):
    """
    Тренування (контест) у форматі ICPC.

    Містить набір задач, перелік команд-учасниць та часові межі.
    """

    title = models.CharField("назва", max_length=200)
    description = models.TextField("опис", blank=True)
    start_at = models.DateTimeField("початок")
    end_at = models.DateTimeField("завершення")
    problems = models.ManyToManyField("training.Problem", verbose_name="задачі", related_name="trainings")
    teams = models.ManyToManyField("training.Team", verbose_name="команди", related_name="trainings", blank=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, verbose_name="створив", null=True, blank=True,
        on_delete=models.SET_NULL, related_name="created_trainings",
    )

    class Meta:
        verbose_name = "тренування"
        verbose_name_plural = "тренування"
        ordering = ["-start_at"]

    def __str__(self):
        """:return: назва тренування"""
        return self.title

    def get_absolute_url(self):
        """:return: адреса сторінки тренування"""
        return reverse("training:training_detail", args=[self.pk])

    @property
    def status(self):
        """
        Визначає стан тренування відносно поточного часу.

        :return: «upcoming», «running» або «finished»
        """
        now = timezone.now()
        if now < self.start_at:
            return "upcoming"
        if now <= self.end_at:
            return "running"
        return "finished"

    @property
    def duration_minutes(self):
        """:return: тривалість тренування у хвилинах"""
        return int((self.end_at - self.start_at).total_seconds() // 60)

    def lettered_problems(self):
        """
        Призначає задачам літери A, B, C… як на контестах ICPC.

        :return: список пар (літера, задача)
        """
        problems = self.problems.order_by("rating", "pk")
        return [(chr(ord("A") + index), problem) for index, problem in enumerate(problems)]
