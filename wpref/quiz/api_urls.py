from django.urls import path
from rest_framework.routers import DefaultRouter

from .views import QuizStartView, QuizAttemptView, QuizCloseView, QuizSummaryView, QuizViewSet

app_name = "quiz_api"

router = DefaultRouter()
# -> /api/quiz/ et /api/quiz/{slug}/...
router.register(r"", QuizViewSet, basename="quiz")

urlpatterns = router.urls + [
    path("<slug:slug>/start/", QuizStartView.as_view(), name="quiz-start"),
    path("<uuid:quiz_id>/attempt/<int:question_order>/", QuizAttemptView.as_view(), name="quiz-attempt", ),
    path("<uuid:quiz_id>/close/", QuizCloseView.as_view(), name="quiz-close", ),
    path("<uuid:quiz_id>/summary/", QuizSummaryView.as_view(), name="quiz-summary", ),
]
