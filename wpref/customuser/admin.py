from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import Group
from django.utils.translation import gettext_lazy as _

from .models import CustomUser


class CustomUserAdmin(UserAdmin):
    model = CustomUser
    list_display = (
        'username', 'email', 'first_name', 'last_name', 'language', 'email_confirmed', 'password_change_required',
        'current_domain', 'is_active', 'is_superuser',)
    list_filter = ('is_staff', 'is_superuser', 'is_active', 'email_confirmed', 'must_change_password', 'current_domain')
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        (_('Personal info'), {'fields': ('first_name', 'last_name', 'email', 'language', 'email_confirmed')}),
        (_('Domains'), {'fields': ('current_domain', 'owned_domains_display', 'managed_domains_display', 'linked_domains_display')}),
        (_('Security'), {'fields': ('must_change_password', 'password_change_required')}),
        (_('Permissions'), {'fields': ('is_active', 'is_staff', 'is_superuser',)}),
        (_('Important dates'), {'fields': ('last_login', 'date_joined')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'password1', 'password2'),
        }),
    )
    search_fields = ('username', 'first_name', 'last_name', 'email')
    ordering = ('username',)
    readonly_fields = ('password_change_required', 'owned_domains_display', 'managed_domains_display', 'linked_domains_display')
    autocomplete_fields = ('current_domain',)

    @admin.display(description=_('Password change required'), boolean=True)
    def password_change_required(self, obj: CustomUser) -> bool:
        return obj.requires_password_change

    @admin.display(description=_('Owned domains'))
    def owned_domains_display(self, obj: CustomUser) -> str:
        return self._render_domains(obj.owned_domains.all())

    @admin.display(description=_('Managed domains'))
    def managed_domains_display(self, obj: CustomUser) -> str:
        return self._render_domains(obj.managed_domains.all())

    @admin.display(description=_('Linked domains'))
    def linked_domains_display(self, obj: CustomUser) -> str:
        return self._render_domains(obj.linked_domains.all())

    @staticmethod
    def _render_domains(domains) -> str:
        items = []
        for domain in domains:
            label = domain.safe_translation_getter('name', any_language=True) or f'Domain#{domain.pk}'
            items.append(label)
        return ', '.join(items) if items else '-'


admin.site.register(CustomUser, CustomUserAdmin)
admin.site.unregister(Group)
