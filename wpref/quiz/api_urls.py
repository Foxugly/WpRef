from django.urls import path
from rest_framework.routers import DefaultRouter

from .views import QuizCreateView, QuizSessionView, QuizSessionStartView, QuizAttemptView, QuizCloseView, QuizSummaryView, QuizViewSet

app_name = "quiz_api"

router = DefaultRouter()
# -> /api/quiz/ et /api/quiz/{slug}/...
router.register(r"", QuizViewSet, basename="quiz")

urlpatterns = router.urls + [
    path("<slug:slug>/create/", QuizCreateView.as_view(), name="quiz-create"),
    path("<int:quiz_id>/start/", QuizSessionStartView.as_view(), name="quiz-start", ),
    path("<int:quiz_id>/attempt/<int:question_order>/", QuizAttemptView.as_view(), name="quiz-attempt"),
    path("<int:quiz_id>/close/", QuizCloseView.as_view(), name="quiz-close"),
    path("<int:quiz_id>/summary/", QuizSummaryView.as_view(), name="quiz-summary"),
]
