import requests
from django.test import TestCase

from training.models import Attempt
from training.services import CodeforcesClient, CodeforcesError, ProblemImporter, SubmissionSynchronizer

from .helpers import make_problem, make_user


class FakeResponse:
    """Імітація відповіді HTTP."""

    def __init__(self, data):
        self._data = data

    def json(self):
        return self._data


class FakeSession:
    """Імітація HTTP-сесії, що повертає заздалегідь задані дані."""

    def __init__(self, data=None, error=None):
        self.data, self.error, self.calls = data, error, []

    def get(self, url, params=None, timeout=None):
        self.calls.append((url, params))
        if self.error:
            raise self.error
        return FakeResponse(self.data)


def submission(sub_id, contest, index, verdict, time=1_700_000_000):
    """Формує посилку у форматі Codeforces API."""
    return {"id": sub_id, "creationTimeSeconds": time, "verdict": verdict,
            "problem": {"contestId": contest, "index": index}}


class CodeforcesClientTests(TestCase):
    """Тести клієнта Codeforces API з підміною мережі."""

    def test_failed_status_raises(self):
        """ТВ-2.1: статус FAILED перетворюється на CodeforcesError з коментарем API."""
        client = CodeforcesClient(session=FakeSession({"status": "FAILED", "comment": "handle not found"}))
        with self.assertRaisesMessage(CodeforcesError, "handle not found"):
            client.get_user_submissions("nobody")

    def test_network_error_raises(self):
        """ТВ-2.2: мережева помилка перетворюється на CodeforcesError."""
        client = CodeforcesClient(session=FakeSession(error=requests.ConnectionError()))
        with self.assertRaises(CodeforcesError):
            client.get_problems()

    def test_import_problems_filters_by_rating(self):
        """ТВ-2.3: імпорт з Codeforces враховує межі складності та ліміт."""
        problems = [{"contestId": 1, "index": "A", "name": "Easy", "rating": 800, "tags": ["math"]},
                    {"contestId": 2, "index": "B", "name": "Hard", "rating": 2500, "tags": []},
                    {"contestId": 3, "index": "C", "name": "NoRating", "tags": []}]
        session = FakeSession({"status": "OK", "result": {"problems": problems}})
        created = ProblemImporter().import_from_codeforces(CodeforcesClient(session=session), ["math"], 800, 1500, 10)
        self.assertEqual(created, 1)
        self.assertEqual(session.calls[0][1], {"tags": "math"})

    def test_sync_creates_attempts_and_skips_duplicates(self):
        """ТВ-2.4: синхронізація створює спроби, пропускає помилки компіляції та дублікати."""
        user = make_user("cf", codeforces_handle="tester")
        make_problem("Watermelon", 800, 4, "A")
        result = [submission(1, 4, "A", "WRONG_ANSWER"), submission(2, 4, "A", "OK"),
                  submission(3, 4, "A", "COMPILATION_ERROR"), submission(4, 999, "Z", "OK")]
        client = CodeforcesClient(session=FakeSession({"status": "OK", "result": result}))
        synchronizer = SubmissionSynchronizer(client)
        self.assertEqual(synchronizer.sync_user(user), 2)
        self.assertEqual(synchronizer.sync_user(user), 0)
        self.assertEqual(sorted(Attempt.objects.values_list("verdict", flat=True)), ["ok", "wrong"])

    def test_same_submission_is_not_imported_for_second_user(self):
        """ТВ-2.5: одна посилка не імпортується двічі навіть для різних користувачів."""
        first = make_user("u1", codeforces_handle="tester")
        second = make_user("u2", codeforces_handle="tester2")
        make_problem("Watermelon", 800, 4, "A")
        data = {"status": "OK", "result": [submission(10, 4, "A", "OK")]}
        self.assertEqual(SubmissionSynchronizer(CodeforcesClient(session=FakeSession(data))).sync_user(first), 1)
        self.assertEqual(SubmissionSynchronizer(CodeforcesClient(session=FakeSession(data))).sync_user(second), 0)
        self.assertEqual(Attempt.objects.count(), 1)
