import csv
import io
import json

from django.db import transaction

from training.models import Problem, Tag

from .exceptions import CodeforcesError, ImportFormatError


class ProblemImporter:
    """
    Імпорт та експорт банку задач.

    Підтримує файли JSON і CSV, а також завантаження задач з Codeforces.
    """

    CSV_FIELDS = ["title", "source", "cf_contest_id", "cf_index", "rating", "tags", "url", "statement"]
    MIN_RATING, MAX_RATING = 800, 3500

    def __init__(self, author=None):
        """
        :param author: користувач, від імені якого створюються задачі
        """
        self._author = author

    @transaction.atomic
    def save_problem(self, data):
        """
        Створює задачу або оновлює наявну задачу Codeforces.

        :param data: словник з полями задачі
        :return: пара (задача, ознака створення)
        :raises ImportFormatError: якщо запис не є об'єктом, відсутня назва або числові поля некоректні
        """
        if not isinstance(data, dict):
            raise ImportFormatError("кожен запис має бути об'єктом з полями задачі")
        title = str(data.get("title", "")).strip()
        if not title:
            raise ImportFormatError("у записі відсутня назва задачі")
        try:
            contest_id = int(data["cf_contest_id"]) if data.get("cf_contest_id") else None
            rating = int(data["rating"]) if data.get("rating") else None
        except (TypeError, ValueError) as error:
            raise ImportFormatError(f"некоректне число в записі «{title}»") from error
        if rating is not None and not self.MIN_RATING <= rating <= self.MAX_RATING:
            raise ImportFormatError(f"складність задачі «{title}» має бути в межах {self.MIN_RATING}–{self.MAX_RATING}")
        source = Problem.Source.CODEFORCES if contest_id else Problem.Source.MANUAL
        values = {
            "title": title,
            "rating": rating,
            "url": data.get("url", "") or "",
            "statement": data.get("statement", "") or "",
            "created_by": self._author,
        }
        if source == Problem.Source.CODEFORCES:
            problem, created = Problem.objects.update_or_create(
                source=source, cf_contest_id=contest_id, cf_index=str(data.get("cf_index", "")).upper(),
                defaults=values,
            )
        else:
            problem, created = Problem.objects.create(source=source, **values), True
        tag_names = data.get("tags") or []
        if isinstance(tag_names, str):
            tag_names = tag_names.split(";")
        if not isinstance(tag_names, list):
            raise ImportFormatError(f"теги задачі «{title}» мають бути списком або рядком")
        cleaned_names = {str(name).strip() for name in tag_names if str(name).strip()}
        tags = [Tag.objects.get_or_create(name=name)[0] for name in sorted(cleaned_names)]
        problem.tags.set(tags)
        return problem, created

    @transaction.atomic
    def import_json(self, stream):
        """
        Імпортує задачі з JSON-файлу (масив об'єктів).

        Імпорт атомарний: у разі помилки в будь-якому записі жодна задача не зберігається.

        :param stream: файловий потік
        :return: кількість нових задач
        :raises ImportFormatError: якщо файл не є коректним JSON-масивом
        """
        try:
            records = json.load(io.TextIOWrapper(stream, encoding="utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError) as error:
            raise ImportFormatError("файл не є коректним JSON") from error
        if not isinstance(records, list):
            raise ImportFormatError("очікується масив задач")
        return sum(1 for record in records if self.save_problem(record)[1])

    @transaction.atomic
    def import_csv(self, stream):
        """
        Імпортує задачі з CSV-файлу з заголовком.

        Імпорт атомарний: у разі помилки в будь-якому рядку жодна задача не зберігається.

        :param stream: файловий потік
        :return: кількість нових задач
        :raises ImportFormatError: якщо бракує обов'язкових стовпців
        """
        try:
            reader = csv.DictReader(io.TextIOWrapper(stream, encoding="utf-8-sig"))
            if not reader.fieldnames or "title" not in reader.fieldnames:
                raise ImportFormatError("у CSV немає стовпця title")
            return sum(1 for row in reader if self.save_problem(row)[1])
        except UnicodeDecodeError as error:
            raise ImportFormatError("файл має бути в кодуванні UTF-8") from error

    def export_json(self, problems):
        """
        Експортує задачі у JSON.

        :param problems: набір задач
        :return: JSON-рядок
        """
        return json.dumps([self._to_dict(problem) for problem in problems], ensure_ascii=False, indent=2)

    def export_csv(self, problems):
        """
        Експортує задачі у CSV.

        :param problems: набір задач
        :return: CSV-рядок
        """
        buffer = io.StringIO()
        writer = csv.DictWriter(buffer, fieldnames=self.CSV_FIELDS)
        writer.writeheader()
        for problem in problems:
            row = self._to_dict(problem)
            row["tags"] = ";".join(row["tags"])
            writer.writerow(row)
        return buffer.getvalue()

    def import_from_codeforces(self, client, tags=None, min_rating=800, max_rating=3500, limit=50):
        """
        Завантажує задачі з архіву Codeforces за фільтрами.

        :param client: екземпляр CodeforcesClient
        :param tags: список тегів
        :param min_rating: мінімальна складність
        :param max_rating: максимальна складність
        :param limit: максимальна кількість задач
        :return: кількість нових задач
        :raises CodeforcesError: у разі помилки API
        """
        created = 0
        selected = [
            item for item in client.get_problems(tags)
            if item.get("rating") and min_rating <= item["rating"] <= max_rating
        ][:limit]
        if not selected:
            raise CodeforcesError("за вказаними фільтрами задач не знайдено")
        for item in selected:
            _, is_new = self.save_problem({
                "title": item["name"],
                "cf_contest_id": item["contestId"],
                "cf_index": item["index"],
                "rating": item["rating"],
                "tags": item.get("tags", []),
            })
            created += is_new
        return created

    @staticmethod
    def _to_dict(problem):
        """
        Перетворює задачу на словник для експорту.

        :param problem: задача
        :return: словник полів
        """
        return {
            "title": problem.title,
            "source": problem.source,
            "cf_contest_id": problem.cf_contest_id or "",
            "cf_index": problem.cf_index,
            "rating": problem.rating or "",
            "tags": [tag.name for tag in problem.tags.all()],
            "url": problem.url,
            "statement": problem.statement,
        }
