from django.db import models


class Tag(models.Model):
    """Тема (тег) задачі, наприклад «greedy» або «graphs»."""

    name = models.CharField("назва", max_length=50, unique=True)

    class Meta:
        verbose_name = "тег"
        verbose_name_plural = "теги"
        ordering = ["name"]

    def __str__(self):
        """:return: назва тегу"""
        return self.name
