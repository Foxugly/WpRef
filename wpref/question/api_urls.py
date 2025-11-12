# question/api_urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import SubjectViewSet, QuestionViewSet

router = DefaultRouter()
router.register(r"subject", SubjectViewSet, basename="subject")
router.register(r"question", QuestionViewSet, basename="question")

urlpatterns = [path("", include(router.urls))]
