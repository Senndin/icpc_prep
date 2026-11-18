from django.contrib import admin

from .models import Attempt, Problem, Tag, Team, Training


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    """Адмін-панель тегів."""

    search_fields = ("name",)


@admin.register(Problem)
class ProblemAdmin(admin.ModelAdmin):
    """Адмін-панель задач."""

    list_display = ("title", "code", "rating", "source")
    list_filter = ("source", "tags")
    search_fields = ("title",)


@admin.register(Team)
class TeamAdmin(admin.ModelAdmin):
    """Адмін-панель команд."""

    list_display = ("name", "coach", "university")
    filter_horizontal = ("members",)


@admin.register(Training)
class TrainingAdmin(admin.ModelAdmin):
    """Адмін-панель тренувань."""

    list_display = ("title", "start_at", "end_at")
    filter_horizontal = ("problems", "teams")


@admin.register(Attempt)
class AttemptAdmin(admin.ModelAdmin):
    """Адмін-панель спроб."""

    list_display = ("user", "problem", "verdict", "submitted_at", "source")
    list_filter = ("verdict", "source")
