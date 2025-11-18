from rest_framework.routers import DefaultRouter

from .views import SubjectViewSet

app_name = 'subject_api'
router = DefaultRouter()
router.register(r"", SubjectViewSet, basename="subject")

urlpatterns = router.urls