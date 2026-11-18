from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import User


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    """Адмін-панель користувачів з полями ролі та хендла."""

    list_display = ("username", "first_name", "last_name", "role", "codeforces_handle")
    list_filter = ("role", "is_active")
    fieldsets = UserAdmin.fieldsets + (("ICPC Prep", {"fields": ("role", "codeforces_handle")}),)
