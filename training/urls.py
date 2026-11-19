from django.urls import path

from .views import dashboard, pages, problems, teams, trainings, transfer

app_name = "training"

urlpatterns = [
    path("", dashboard.DashboardView.as_view(), name="dashboard"),
    path("about/", pages.AboutView.as_view(), name="about"),
    # Банк задач
    path("problems/", problems.ProblemListView.as_view(), name="problem_list"),
    path("problems/new/", problems.ProblemCreateView.as_view(), name="problem_create"),
    path("problems/import/", transfer.ProblemImportView.as_view(), name="problem_import"),
    path("problems/export/", transfer.ProblemExportView.as_view(), name="problem_export"),
    path("problems/codeforces/", transfer.CodeforcesImportView.as_view(), name="codeforces_import"),
    path("problems/<int:pk>/", problems.ProblemDetailView.as_view(), name="problem_detail"),
    path("problems/<int:pk>/edit/", problems.ProblemUpdateView.as_view(), name="problem_update"),
    path("problems/<int:pk>/delete/", problems.ProblemDeleteView.as_view(), name="problem_delete"),
    path("problems/<int:pk>/attempt/", problems.AttemptCreateView.as_view(), name="attempt_create"),
    # Команди
    path("teams/", teams.TeamListView.as_view(), name="team_list"),
    path("teams/new/", teams.TeamCreateView.as_view(), name="team_create"),
    path("teams/<int:pk>/", teams.TeamDetailView.as_view(), name="team_detail"),
    path("teams/<int:pk>/edit/", teams.TeamUpdateView.as_view(), name="team_update"),
    path("teams/<int:pk>/delete/", teams.TeamDeleteView.as_view(), name="team_delete"),
    # Тренування
    path("trainings/", trainings.TrainingListView.as_view(), name="training_list"),
    path("trainings/new/", trainings.TrainingCreateView.as_view(), name="training_create"),
    path("trainings/<int:pk>/", trainings.TrainingDetailView.as_view(), name="training_detail"),
    path("trainings/<int:pk>/edit/", trainings.TrainingUpdateView.as_view(), name="training_update"),
    path("trainings/<int:pk>/delete/", trainings.TrainingDeleteView.as_view(), name="training_delete"),
]
