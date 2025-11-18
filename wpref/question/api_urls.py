from rest_framework.routers import DefaultRouter
from .views import  QuestionViewSet
app_name = "question_api"

router = DefaultRouter()
router.register(r"", QuestionViewSet, basename="question")

urlpatterns = router.urls