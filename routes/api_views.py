# routes/api_views.py

from django.shortcuts    import get_object_or_404
from django.db.models    import Max

from rest_framework      import viewsets, mixins, permissions
from rest_framework.authentication import SessionAuthentication, TokenAuthentication

from .models             import Route, RoutePoint
from .serializers        import RouteSerializer, RoutePointSerializer

from .permissions        import IsRouteOwner

class RouteViewSet(viewsets.ModelViewSet):
    """
    API dla tras – tylko trasy właściciela.
    """
    serializer_class   = RouteSerializer
    permission_classes = [permissions.IsAuthenticated]
    authentication_classes = [
        TokenAuthentication
    ]
    http_method_names  = ["get", "post", "patch", "delete", "put"]

    def get_queryset(self):
        return Route.objects.filter(owner=self.request.user).order_by("-created")

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)


class RoutePointViewSet(
    mixins.CreateModelMixin,
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.UpdateModelMixin,
    mixins.DestroyModelMixin,
    viewsets.GenericViewSet
):
    """
    API dla punktów danej trasy – tylko punkty tras właściciela.
    """
    serializer_class   = RoutePointSerializer
    permission_classes = [permissions.IsAuthenticated, IsRouteOwner]
    authentication_classes = [
        TokenAuthentication,
        SessionAuthentication
    ]
    http_method_names  = ["get", "post", "patch", "delete"]

    def get_queryset(self):
        return RoutePoint.objects.filter(
            route__owner=self.request.user,
            route_id=self.kwargs["route_pk"]
        ).order_by("order")

    def perform_create(self, serializer):
        # upewniamy się, że trasa należy do request.user
        route = get_object_or_404(
            Route,
            pk=self.kwargs["route_pk"],
            owner=self.request.user
        )
        # obliczamy kolejny order
        last = (
            RoutePoint.objects.filter(route=route)
            .aggregate(max_order=Max("order"))["max_order"]
            or 0
        )
        serializer.save(route=route, order=last + 1)
