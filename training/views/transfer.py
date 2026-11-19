from django.contrib import messages
from django.http import HttpResponse
from django.shortcuts import redirect
from django.utils import timezone
from django.views import View
from django.views.generic import FormView

from accounts.mixins import ManagerRequiredMixin
from training.forms import CodeforcesImportForm, ImportFileForm
from training.models import Problem
from training.services import CodeforcesClient, CodeforcesError, ImportFormatError, ProblemImporter


class ProblemImportView(ManagerRequiredMixin, FormView):
    """Імпорт задач з файлу JSON або CSV."""

    form_class = ImportFileForm
    template_name = "training/problem_import.html"

    def form_valid(self, form):
        """
        Читає файл і створює задачі.

        :param form: валідна форма з файлом
        :return: перенаправлення на банк задач або повторний показ форми
        """
        uploaded = form.cleaned_data["file"]
        importer = ProblemImporter(author=self.request.user)
        try:
            if uploaded.name.lower().endswith(".json"):
                created = importer.import_json(uploaded.file)
            else:
                created = importer.import_csv(uploaded.file)
        except ImportFormatError as error:
            messages.error(self.request, f"Помилка імпорту: {error}")
            return self.form_invalid(form)
        messages.success(self.request, f"Імпорт завершено. Нових задач: {created}.")
        return redirect("training:problem_list")


class ProblemExportView(ManagerRequiredMixin, View):
    """Експорт банку задач у файл."""

    def get(self, request):
        """
        Формує файл для завантаження.

        :param request: HTTP-запит з параметром format (json або csv)
        :return: HTTP-відповідь з файлом
        """
        file_format = request.GET.get("format", "json")
        importer = ProblemImporter()
        problems = Problem.objects.prefetch_related("tags")
        stamp = timezone.localtime().strftime("%Y%m%d")
        if file_format == "csv":
            content, mime = importer.export_csv(problems), "text/csv"
        else:
            file_format, content, mime = "json", importer.export_json(problems), "application/json"
        response = HttpResponse(content, content_type=f"{mime}; charset=utf-8")
        response["Content-Disposition"] = f'attachment; filename="problems_{stamp}.{file_format}"'
        return response


class CodeforcesImportView(ManagerRequiredMixin, FormView):
    """Завантаження задач з архіву Codeforces."""

    form_class = CodeforcesImportForm
    template_name = "training/codeforces_import.html"

    def form_valid(self, form):
        """
        Звертається до Codeforces API та зберігає задачі.

        :param form: валідна форма фільтрів
        :return: перенаправлення на банк задач або повторний показ форми
        """
        data = form.cleaned_data
        try:
            created = ProblemImporter(author=self.request.user).import_from_codeforces(
                CodeforcesClient(), data["tag_list"], data["min_rating"], data["max_rating"], data["limit"]
            )
        except CodeforcesError as error:
            messages.error(self.request, f"Codeforces: {error}")
            return self.form_invalid(form)
        messages.success(self.request, f"З Codeforces завантажено нових задач: {created}.")
        return redirect("training:problem_list")
