from django.core.management.base import BaseCommand

from accounts.models import User
from training.services import CodeforcesClient, CodeforcesError, SubmissionSynchronizer


class Command(BaseCommand):
    """Синхронізує спроби всіх студентів з Codeforces (для планувальника завдань)."""

    help = "Завантажує посилки з Codeforces для всіх студентів із заповненим хендлом"

    def handle(self, *args, **options):
        """Виконує синхронізацію для кожного студента."""
        synchronizer = SubmissionSynchronizer(CodeforcesClient())
        for user in User.objects.filter(role=User.Role.STUDENT).exclude(codeforces_handle=""):
            try:
                created = synchronizer.sync_user(user)
                self.stdout.write(f"{user.codeforces_handle}: нових спроб {created}")
            except CodeforcesError as error:
                self.stderr.write(f"{user.codeforces_handle}: помилка — {error}")
