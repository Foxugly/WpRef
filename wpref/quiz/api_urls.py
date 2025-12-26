from django.urls import path

from .views import QuizTemplateViewSet, QuizViewSet, QuizQuestionAnswerViewSet, QuizTemplateQuizQuestionViewSet

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
    #     # Quiz -> answers
    path("<int:quiz_id>/answer/", quiz_answer_list, name="quiz-answer-list"),
    path("<int:quiz_id>/answer/<int:answer_id>/", quiz_answer_detail, name="quiz-answer-detail"),
]
