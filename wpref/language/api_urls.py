# lang/api_urls.py (ou urls.py)
from rest_framework.routers import DefaultRouter

from .views import LanguageViewSet

app_name = "lang-api"

router = DefaultRouter()
router.register(r"", LanguageViewSet, basename="lang")

urlpatterns = router.urls
