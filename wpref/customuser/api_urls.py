from django.urls import path
from rest_framework.routers import DefaultRouter

from .views import CustomUserViewSet, UserQuizListView, PasswordChangeView, PasswordResetConfirmView, PasswordResetRequestView

app_name = "user-api"

router = DefaultRouter()
router.register("", CustomUserViewSet, basename="user")


user_me = CustomUserViewSet.as_view({"get": "me"})
user_me_current_domain = CustomUserViewSet.as_view({"post": "set_current_domain"})

urlpatterns = router.urls + [
    # Liste des quiz liés à cet utilisateur
    path("<int:pk>/quizzes/", UserQuizListView.as_view(), name="user-quizzes", ),
    path("password/reset/", PasswordResetRequestView.as_view(), name="password-reset"),
    path("password/reset/confirm/", PasswordResetConfirmView.as_view(), name="password-reset-confirm"),
    path("password/change/", PasswordChangeView.as_view(), name="password-change"),
    path("me/", user_me, name="me"),
    path("me/current-domain/", user_me_current_domain, name="user-me-current-domain"),
]
