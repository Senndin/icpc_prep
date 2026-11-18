from django.contrib.auth import views as auth_views
from django.urls import path

from . import views

app_name = "accounts"

urlpatterns = [
    path("login/", auth_views.LoginView.as_view(template_name="accounts/login.html"), name="login"),
    path("logout/", auth_views.LogoutView.as_view(), name="logout"),
    path("register/", views.RegisterView.as_view(), name="register"),
    path("profile/", views.ProfileView.as_view(), name="profile"),
    path("profile/sync/", views.SyncCodeforcesView.as_view(), name="sync"),
    path("users/", views.UserListView.as_view(), name="users"),
    path("users/<int:pk>/role/", views.UserRoleUpdateView.as_view(), name="user_role"),
]
