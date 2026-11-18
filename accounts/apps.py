from django.apps import AppConfig


class AccountsConfig(AppConfig):
    """Конфігурація застосунку облікових записів."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "accounts"
    verbose_name = "Користувачі"
