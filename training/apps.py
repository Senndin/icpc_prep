from django.apps import AppConfig


class TrainingConfig(AppConfig):
    """Конфігурація застосунку підготовки до олімпіад."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "training"
    verbose_name = "Підготовка до ICPC"
