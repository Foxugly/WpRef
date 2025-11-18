from django.urls import path
from .views import QuizStartView, QuizAttemptView, QuizCloseView, QuizQuestionDetailView, QuizSummaryView
app_name = "quiz_api"

urlpatterns = [
    path("<slug:slug>/start/", QuizStartView.as_view(), name="quiz-start"),
    path("<uuid:quiz_id>/question/<int:question_order>/", QuizQuestionDetailView.as_view(), name="quiz-question-detail",),
    path("<uuid:quiz_id>/attempt/<int:question_order>/", QuizAttemptView.as_view(), name="quiz-attempt",),
    path("<uuid:quiz_id>/close/", QuizCloseView.as_view(), name="quiz-close",),
    path("<uuid:quiz_id>/summary/", QuizSummaryView.as_view(), name="quiz-summary", ),
]
