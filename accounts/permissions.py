from rest_framework.permissions import BasePermission


class IsAdminUser(BasePermission):
    """
    Allows access only to authenticated administrative users.
    """

    message = "Administrator access is required."

    def has_permission(self, request, view):
        user = request.user

        return bool(
            user
            and user.is_authenticated
            and user.is_active
            and user.is_admin_user
        )


class IsAssociateUser(BasePermission):
    """
    Allows access only to authenticated associates.
    """

    message = "Associate access is required."

    def has_permission(self, request, view):
        user = request.user

        return bool(
            user
            and user.is_authenticated
            and user.is_associate_user
        )


class IsAdminOrAssociate(BasePermission):
    """
    Allows either authenticated administrative users
    or authenticated associates.
    """

    message = "Authenticated access is required."

    def has_permission(self, request, view):
        user = request.user

        return bool(
            user
            and user.is_authenticated
            and user.is_active
            and (
                user.is_admin_user
                or user.is_associate_user
            )
        )