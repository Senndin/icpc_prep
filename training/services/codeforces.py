import requests
from django.conf import settings

from .exceptions import CodeforcesError


class CodeforcesClient:
    """
    Клієнт відкритого Codeforces API.

    Використовує лише публічні методи, які не потребують ключа:
    problemset.problems та user.status.
    """

    def __init__(self, base_url=None, timeout=None, session=None):
        """
        Створює клієнт.

        :param base_url: базова адреса API
        :param timeout: тайм-аут запиту в секундах
        :param session: HTTP-сесія (для підміни в тестах)
        """
        self._base_url = base_url or settings.CODEFORCES_API_URL
        self._timeout = timeout or settings.CODEFORCES_TIMEOUT
        self._session = session or requests.Session()

    def _call(self, method, **params):
        """
        Виконує запит до методу API.

        :param method: назва методу API
        :param params: параметри запиту
        :return: поле result відповіді
        :raises CodeforcesError: у разі мережевої помилки або статусу FAILED
        """
        try:
            response = self._session.get(self._base_url + method, params=params, timeout=self._timeout)
            data = response.json()
        except (requests.RequestException, ValueError) as error:
            raise CodeforcesError("сервер Codeforces недоступний") from error
        if data.get("status") != "OK":
            raise CodeforcesError(data.get("comment", "невідома помилка API"))
        return data["result"]

    def get_problems(self, tags=None):
        """
        Отримує задачі з архіву Codeforces.

        :param tags: список тегів для фільтрації
        :return: список словників задач
        """
        params = {"tags": ";".join(tags)} if tags else {}
        return self._call("problemset.problems", **params)["problems"]

    def get_user_submissions(self, handle, count=500):
        """
        Отримує останні посилки користувача.

        :param handle: хендл на Codeforces
        :param count: максимальна кількість посилок
        :return: список словників посилок
        """
        return self._call("user.status", handle=handle, count=count)
