from rest_framework import permissions
from .models import Route

class IsRouteOwner(permissions.BasePermission):
    """
    Pozwala tylko właścicielowi trasy operować na jej punktach.
    """
    def has_permission(self, request, view):
        route_pk = view.kwargs.get('route_pk')
        if route_pk is None:
            return False
        return Route.objects.filter(pk=route_pk, owner=request.user).exists()

    def has_object_permission(self, request, view, obj):
        return obj.route.owner == request.user