from django.contrib.auth.models import AbstractUser
from django.core.validators import RegexValidator
from django.db import models


class User(AbstractUser):
    """
    Користувач системи з роллю.

    Розширює стандартного користувача Django полями ролі
    та хендла на Codeforces.
    """

    class Role(models.TextChoices):
        """Перелік ролей користувачів."""

        STUDENT = "student", "Студент"
        COACH = "coach", "Тренер"
        ADMIN = "admin", "Адміністратор"

    role = models.CharField(
        "роль", max_length=10, choices=Role.choices, default=Role.STUDENT
    )
    codeforces_handle = models.CharField(
        "хендл Codeforces",
        max_length=24,
        blank=True,
        validators=[RegexValidator(r"^[A-Za-z0-9_.\-]*$", "Недопустимі символи в хендлі.")],
    )

    class Meta:
        verbose_name = "користувач"
        verbose_name_plural = "користувачі"
        ordering = ["last_name", "first_name", "username"]

    def __str__(self):
        """
        Повертає ім'я для відображення.

        :return: повне ім'я або логін
        """
        return self.get_full_name() or self.username

    @property
    def is_student(self):
        """:return: True, якщо користувач — студент"""
        return self.role == self.Role.STUDENT

    @property
    def is_coach(self):
        """:return: True, якщо користувач — тренер"""
        return self.role == self.Role.COACH

    @property
    def is_admin_role(self):
        """:return: True, якщо користувач — адміністратор (роль або суперкористувач)"""
        return self.role == self.Role.ADMIN or self.is_superuser

    @property
    def can_manage(self):
        """
        Перевіряє право на керування задачами, командами та тренуваннями.

        :return: True для тренера та адміністратора
        """
        return self.is_coach or self.is_admin_role

    @property
    def team(self):
        """
        Повертає команду студента.

        :return: об'єкт Team або None
        """
        return self.teams.first()
