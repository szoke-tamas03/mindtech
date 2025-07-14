from rest_framework import permissions

class IsRestaurantUser(permissions.BasePermission):
    """
    Csak akkor enged, ha a felhasználó étterem (is_restaurant)
    """

    def has_permission(self, request, view):
        return bool(
            request.user and
            request.user.is_authenticated and
            getattr(request.user, 'is_restaurant', False)
        )