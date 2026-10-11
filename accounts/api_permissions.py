from rest_framework.permissions import BasePermission


class IsAdminOrReadOnly(BasePermission):
    """
    Anyone may read the resource.

    Only administrative users may create, update, or delete it.
    """

    message = "Administrator access is required for this action."

    SAFE_METHODS = ("GET", "HEAD", "OPTIONS")

    def has_permission(self, request, view):
        if request.method in self.SAFE_METHODS:
            return True

        user = request.user

        return bool(
            user
            and user.is_authenticated
            and user.is_active
            and user.is_admin_user
        )