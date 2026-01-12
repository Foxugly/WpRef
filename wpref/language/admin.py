# lang/admin.py
from django.contrib import admin

from .models import Language


@admin.register(Language)
class LangAdmin(admin.ModelAdmin):
    list_display = ("id", "code", "name", "active",)
    list_filter = ("active",)
    search_fields = ("code", "name",)
    ordering = ("code",)
    list_editable = ("active",)
