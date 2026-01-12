from django.urls import path

from .views import TranslateBatchView

app_name = 'translate-api'

urlpatterns = [
    path("batch/", TranslateBatchView.as_view(), name="translate-batch"),
]
