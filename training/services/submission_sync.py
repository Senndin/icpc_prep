from datetime import datetime, timezone as dt_timezone

from training.models import Attempt, Problem


class SubmissionSynchronizer:
    """Перенесення посилок користувача з Codeforces у спроби системи."""

    # Вердикти, які за правилами ICPC не враховуються як спроба
    IGNORED_VERDICTS = {None, "TESTING", "COMPILATION_ERROR", "SKIPPED"}

    def __init__(self, client):
        """
        :param client: екземпляр CodeforcesClient
        """
        self._client = client

    def sync_user(self, user):
        """
        Синхронізує посилки користувача з задачами банку.

        :param user: користувач з заповненим хендлом
        :return: кількість створених спроб
        :raises CodeforcesError: у разі помилки API
        """
        problems = {
            (problem.cf_contest_id, problem.cf_index): problem
            for problem in Problem.objects.filter(source=Problem.Source.CODEFORCES)
        }
        submissions = self._client.get_user_submissions(user.codeforces_handle)
        # Ідентифікатор посилки унікальний у всій базі, тому перевіряємо його незалежно від користувача
        known_ids = set(
            Attempt.objects.filter(cf_submission_id__in=[item["id"] for item in submissions])
            .values_list("cf_submission_id", flat=True)
        )
        new_attempts = []
        for submission in submissions:
            key = (submission["problem"].get("contestId"), submission["problem"].get("index"))
            verdict = submission.get("verdict")
            if key not in problems or verdict in self.IGNORED_VERDICTS or submission["id"] in known_ids:
                continue
            new_attempts.append(Attempt(
                user=user,
                problem=problems[key],
                verdict=Attempt.Verdict.ACCEPTED if verdict == "OK" else Attempt.Verdict.WRONG,
                submitted_at=datetime.fromtimestamp(submission["creationTimeSeconds"], tz=dt_timezone.utc),
                source=Attempt.Source.CODEFORCES,
                cf_submission_id=submission["id"],
            ))
        Attempt.objects.bulk_create(new_attempts)
        return len(new_attempts)
