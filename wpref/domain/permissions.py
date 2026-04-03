from rest_framework.permissions import BasePermission

from wpref.permissions import is_authenticated_user


class IsDomainOwnerOrStaff(BasePermission):
    def has_object_permission(self, request, view, obj):
        user = request.user
        if not is_authenticated_user(user):
            return False
        if getattr(user, "is_superuser", False):
            return True
        if obj.owner_id == user.id:
            return True
        return obj.staff.filter(id=user.id).exists()
