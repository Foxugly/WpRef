# customuser/api/api_urls.py

from django.urls import path

from .views import *

app_name = "customuser_api"

urlpatterns = [
    # POST Créer un utilisateur
    # GET Liste des utilisateurs (staff/admin only)
    path("", CustomUserListCreateView.as_view(), name="user-list-create"),
    # Récupérer / modifier un utilisateur
    path("<int:pk>/", CustomUserDetailUpdateView.as_view(), name="user-detail-update", ),
    # Liste des quiz liés à cet utilisateur
    path("<int:pk>/quizzes/", UserQuizListView.as_view(), name="user-quizzes", ),
    path("password/reset/", PasswordResetRequestView.as_view(), name="password-reset"),
    path("password/reset/confirm/", PasswordResetConfirmView.as_view(), name="password-reset-confirm"),
    path("password/change/", PasswordChangeView.as_view(), name="password-change"),
    path("me/", MeView.as_view(), name="me"),
]
