"""Власні винятки бізнес-логіки."""


class CodeforcesError(Exception):
    """Помилка звернення до Codeforces API (мережа, ліміт запитів, невірний хендл)."""


class ImportFormatError(Exception):
    """Помилка формату файлу під час імпорту задач."""
