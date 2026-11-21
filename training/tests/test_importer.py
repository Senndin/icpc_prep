import io
import json

from django.test import TestCase

from training.models import Problem
from training.services import ImportFormatError, ProblemImporter

from .helpers import make_problem


def stream(text):
    """Перетворює рядок на байтовий потік, як у завантаженого файлу."""
    return io.BytesIO(text.encode("utf-8"))


class ProblemImporterTests(TestCase):
    """Модульні тести імпорту та експорту банку задач."""

    def test_import_json_creates_problems_with_tags(self):
        """ТВ-4.1: імпорт коректного JSON створює задачі та теги."""
        data = [{"title": "Watermelon", "cf_contest_id": 4, "cf_index": "a", "rating": 800, "tags": ["math"]}]
        created = ProblemImporter().import_json(stream(json.dumps(data)))
        problem = Problem.objects.get()
        self.assertEqual(created, 1)
        self.assertEqual(problem.code, "4A")
        self.assertEqual([t.name for t in problem.tags.all()], ["math"])

    def test_reimport_codeforces_problem_does_not_duplicate(self):
        """ТВ-4.2: повторний імпорт задачі Codeforces оновлює її, а не дублює."""
        data = json.dumps([{"title": "Old", "cf_contest_id": 4, "cf_index": "A"}])
        ProblemImporter().import_json(stream(data))
        created = ProblemImporter().import_json(stream(data.replace("Old", "New")))
        self.assertEqual((created, Problem.objects.count(), Problem.objects.get().title), (0, 1, "New"))

    def test_import_invalid_json_raises(self):
        """ТВ-4.3: некоректний JSON спричиняє виняток ImportFormatError."""
        with self.assertRaises(ImportFormatError):
            ProblemImporter().import_json(stream("{bad"))
        with self.assertRaises(ImportFormatError):
            ProblemImporter().import_json(stream('{"title": "not a list"}'))

    def test_import_record_without_title_raises(self):
        """ТВ-4.4: запис без назви відхиляється."""
        with self.assertRaises(ImportFormatError):
            ProblemImporter().import_json(stream('[{"rating": 800}]'))

    def test_import_csv_with_semicolon_tags(self):
        """ТВ-4.5: імпорт CSV з тегами через крапку з комою."""
        text = "title,cf_contest_id,cf_index,rating,tags\nTaxi,158,B,1100,greedy;implementation\n"
        ProblemImporter().import_csv(stream(text))
        self.assertEqual(Problem.objects.get().tags.count(), 2)

    def test_csv_without_title_column_raises(self):
        """ТВ-4.6: CSV без стовпця title відхиляється."""
        with self.assertRaises(ImportFormatError):
            ProblemImporter().import_csv(stream("name,rating\nX,800\n"))

    def test_export_then_import_roundtrip(self):
        """ТВ-4.7: експортований JSON імпортується без втрат."""
        make_problem("Taxi", 1100, 158, "B")
        exported = ProblemImporter().export_json(Problem.objects.all())
        Problem.objects.all().delete()
        ProblemImporter().import_json(stream(exported))
        self.assertEqual(Problem.objects.get().code, "158B")
        self.assertIn("title,source", ProblemImporter().export_csv(Problem.objects.all()))

    def test_record_that_is_not_object_raises(self):
        """ТВ-4.8: запис, що не є об'єктом, відхиляється без аварійного завершення."""
        with self.assertRaises(ImportFormatError):
            ProblemImporter().import_json(stream("[1, 2, 3]"))

    def test_rating_out_of_range_raises(self):
        """ТВ-4.9: складність поза межами 800–3500 відхиляється."""
        with self.assertRaises(ImportFormatError):
            ProblemImporter().import_json(stream('[{"title": "X", "rating": 100}]'))
        with self.assertRaises(ImportFormatError):
            ProblemImporter().import_csv(stream("title,rating\nX,abc\n"))

    def test_import_is_atomic(self):
        """ТВ-4.10: помилка в одному записі скасовує імпорт усього файлу."""
        data = json.dumps([{"title": "Good", "rating": 800}, {"rating": 900}])
        with self.assertRaises(ImportFormatError):
            ProblemImporter().import_json(stream(data))
        self.assertEqual(Problem.objects.count(), 0)
