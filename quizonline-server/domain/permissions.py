from rest_framework.permissions import BasePermission

from config.permissions import is_authenticated_user


class IsDomainOwnerOrManager(BasePermission):
    """Autorise le superuser Django, le owner du domaine, ou un manager du domaine (Domain.managers M2M)."""
    def has_object_permission(self, request, view, obj):
        user = request.user
        if not is_authenticated_user(user):
            return False
        if getattr(user, "is_superuser", False):
            return True
        if obj.owner_id == user.id:
            return True
        return obj.managers.filter(id=user.id).exists()
