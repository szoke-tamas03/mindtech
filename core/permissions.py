from rest_framework import permissions

class IsRestaurantUser(permissions.BasePermission):
    """
    Only allow access to users who are authenticated and are restaurant owners.
    """

    def has_permission(self, request, view):
        return bool(
            request.user and
            request.user.is_authenticated and
            getattr(request.user, 'is_restaurant', False)
        )