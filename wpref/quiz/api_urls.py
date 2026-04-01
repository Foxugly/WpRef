from django.urls import path

from .views import (
    QuizTemplateViewSet,
    QuizViewSet,
    QuizQuestionAnswerViewSet,
    QuizTemplateQuizQuestionViewSet,
    QuizAlertThreadViewSet,
)

app_name = "quiz-api"
#
# # --- QuizTemplate ---
quiztemplate_list = QuizTemplateViewSet.as_view({"get": "list", "post": "create"})
quiztemplate_detail = QuizTemplateViewSet.as_view({
    "get": "retrieve",
    "put": "update",
    "patch": "partial_update",
    "delete": "destroy",
})
quiztemplate_generate = QuizTemplateViewSet.as_view({"post": "generate_from_subjects"})
# # --- QuizQuestion nested under template ---
template_question_list = QuizTemplateQuizQuestionViewSet.as_view({"get": "list", "post": "create"})
template_question_detail = QuizTemplateQuizQuestionViewSet.as_view({
    "get": "retrieve",
    "put": "update",
    "patch": "partial_update",
    "delete": "destroy",
})

# # --- Quiz sessions ---
quiz_list = QuizViewSet.as_view({"get": "list", "post": "create"})
quiz_detail = QuizViewSet.as_view({
    "get": "retrieve",
    "put": "update",
    "patch": "partial_update",
    "delete": "destroy",
})
quiz_start = QuizViewSet.as_view({"post": "start"})
quiz_close = QuizViewSet.as_view({"post": "close"})
quiz_bulk = QuizViewSet.as_view({"post": "bulk_create_from_template"})
#
# # --- Alert threads ---
quiz_alert_list = QuizAlertThreadViewSet.as_view({"get": "list", "post": "create"})
quiz_alert_detail = QuizAlertThreadViewSet.as_view({"get": "retrieve", "patch": "partial_update"})
quiz_alert_message = QuizAlertThreadViewSet.as_view({"post": "post_message"})
quiz_alert_close = QuizAlertThreadViewSet.as_view({"post": "close"})
quiz_alert_reopen = QuizAlertThreadViewSet.as_view({"post": "reopen"})
quiz_alert_unread_count = QuizAlertThreadViewSet.as_view({"get": "unread_count"})
#
# # --- Answers nested under quiz ---
quiz_answer_list = QuizQuestionAnswerViewSet.as_view({"get": "list", "post": "create"})
quiz_answer_detail = QuizQuestionAnswerViewSet.as_view({
    "get": "retrieve",
    "put": "update",
    "patch": "partial_update",
    "delete": "destroy",
})
#
urlpatterns = [
    #     # QuizTemplate
    path("template/", quiztemplate_list, name="quiz-template-list"),
    path("template/<int:qt_id>/", quiztemplate_detail, name="quiz-template-detail"),
    path("template/generate-from-subjects/", quiztemplate_generate, name="quiz-template-generate-from-subjects"),
    #
    #     # Template -> questions (QuizQuestion)
    path("template/<int:qt_id>/question/", template_question_list, name="quiz-template-question-list"),
    path("template/<int:qt_id>/question/", template_question_list, name="quiz-template-add-question"),
    #
    path("template/<int:qt_id>/question/<int:qq_id>/", template_question_detail, name="quiz-template-question-detail"),
    path("template/<int:qt_id>/question/<int:qq_id>/", template_question_detail, name="quiz-template-update-question"),
    path("template/<int:qt_id>/question/<int:qq_id>/", template_question_detail, name="quiz-template-delete-question"),
    #
    #     # Quiz (sessions)
    path("", quiz_list, name="quiz-list"),
    path("<int:quiz_id>/", quiz_detail, name="quiz-detail"),
    path("bulk-create-from-template/", quiz_bulk, name="quiz-bulk-create-from-template"),
    path("<int:quiz_id>/start/", quiz_start, name="quiz-start"),
    path("<int:quiz_id>/close/", quiz_close, name="quiz-close"),
    #
    #     # Quiz alerts
    path("alerts/", quiz_alert_list, name="quiz-alert-list"),
    path("alerts/unread-count/", quiz_alert_unread_count, name="quiz-alert-unread-count"),
    path("alerts/<int:alert_id>/", quiz_alert_detail, name="quiz-alert-detail"),
    path("alerts/<int:alert_id>/message/", quiz_alert_message, name="quiz-alert-message"),
    path("alerts/<int:alert_id>/close/", quiz_alert_close, name="quiz-alert-close"),
    path("alerts/<int:alert_id>/reopen/", quiz_alert_reopen, name="quiz-alert-reopen"),
    #
    #     # Quiz -> answers
    path("<int:quiz_id>/answer/", quiz_answer_list, name="quiz-answer-list"),
    path("<int:quiz_id>/answer/<int:answer_id>/", quiz_answer_detail, name="quiz-answer-detail"),
]
