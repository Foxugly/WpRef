from rest_framework.permissions import BasePermission


class IsDomainOwnerOrStaff(BasePermission):
    def has_object_permission(self, request, view, obj):
        user = request.user
        if not user or not user.is_authenticated:
            return False
        if user.is_superuser:
            return True

        if user.is_staff:
            return True

        if obj.owner_id == user.id:
            return True

        return obj.staff.filter(id=user.id).exists()
