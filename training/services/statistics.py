from collections import Counter

from training.models import Attempt


class UserStatistics:
    """Обчислення показників прогресу студента."""

    # Межі рівнів складності за рейтингом Codeforces
    LEVELS = (("до 1200", 0, 1199), ("1200–1599", 1200, 1599), ("1600–1999", 1600, 1999), ("2000+", 2000, 9999))

    def __init__(self, user):
        """
        :param user: студент, для якого рахується статистика
        """
        self._attempts = list(
            Attempt.objects.filter(user=user).select_related("problem").prefetch_related("problem__tags")
        )
        accepted = [attempt.problem for attempt in self._attempts if attempt.is_accepted]
        # Множина унікальних розв'язаних задач
        self._solved = {problem.pk: problem for problem in accepted}

    @property
    def solved_count(self):
        """:return: кількість унікальних розв'язаних задач"""
        return len(self._solved)

    @property
    def attempts_count(self):
        """:return: загальна кількість спроб"""
        return len(self._attempts)

    @property
    def accuracy(self):
        """
        Точність: частка зарахованих спроб серед усіх.

        :return: відсоток від 0 до 100
        """
        if not self._attempts:
            return 0
        accepted = sum(1 for attempt in self._attempts if attempt.is_accepted)
        return round(100 * accepted / len(self._attempts))

    @property
    def score(self):
        """
        Бали прогресу: сума рейтингів розв'язаних задач, поділених на 100.

        :return: ціле число балів
        """
        return sum((problem.rating or 800) // 100 for problem in self._solved.values())

    def solved_ids(self):
        """:return: множина id розв'язаних задач"""
        return set(self._solved)

    def by_tag(self, limit=8):
        """
        Розподіл розв'язаних задач за тегами.

        :param limit: кількість найчастіших тегів
        :return: список пар (тег, кількість)
        """
        counter = Counter(tag.name for problem in self._solved.values() for tag in problem.tags.all())
        return counter.most_common(limit)

    def by_level(self):
        """
        Розподіл розв'язаних задач за рівнями складності.

        :return: список пар (рівень, кількість)
        """
        ratings = [problem.rating or 800 for problem in self._solved.values()]
        return [(name, sum(1 for r in ratings if low <= r <= high)) for name, low, high in self.LEVELS]
