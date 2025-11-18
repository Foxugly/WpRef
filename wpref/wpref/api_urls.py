# question/api_urls.py
from django.urls import path, include

app_name = 'api'
urlpatterns = [
    path("subject/", include(("subject.api_urls","subject"), namespace="subject")),
    path("question/", include(("question.api_urls", "question"), namespace="question")),
    path("quiz/", include(("quiz.api_urls", "quiz"), namespace="quiz")),
    path("user/", include(("customuser.api_urls", "user"), namespace="user")),
]
