# routes/api_views.py

from django.shortcuts    import get_object_or_404
from django.db.models    import Max

from rest_framework      import viewsets, mixins, permissions, authentication, status
from rest_framework.authentication import SessionAuthentication, TokenAuthentication
from rest_framework.generics import RetrieveAPIView
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from .models             import Route, RoutePoint, GameBoard
from .serializers        import RouteSerializer, RoutePointSerializer, GameBoardSerializer

from .permissions        import IsRouteOwner



class IsOwner(permissions.BasePermission):
    """Pozwala modyfikować obiekt tylko jego właścicielowi."""
    def has_object_permission(self, request, view, obj):
        return obj.owner == request.user


class RouteViewSet(viewsets.ModelViewSet):
    """
    API dla tras – tylko trasy właściciela.
    """
    serializer_class   = RouteSerializer
    permission_classes = [permissions.IsAuthenticated]
    authentication_classes = [
        TokenAuthentication,
        SessionAuthentication
    ]
    http_method_names  = ["get", "post", "patch", "delete", "put"]

    def get_queryset(self):
        return (
            Route.objects
            .filter(owner=self.request.user)
            .prefetch_related("points")    # jeden SELECT na punkty
            .order_by("-created")
        )

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

class RoutePointBulkView(APIView):
    permission_classes = [permissions.IsAuthenticated, IsRouteOwner]
    authentication_classes = [TokenAuthentication, SessionAuthentication]

    def put(self, request, route_pk):
        route = get_object_or_404(Route, pk=route_pk, owner=request.user)
        RoutePoint.objects.filter(route=route).delete()
        points = request.data
        objs = []
        for idx, pt in enumerate(points):
            objs.append(RoutePoint(
                route=route,
                x=pt.get("x"),
                y=pt.get("y"),
                order=idx + 1
            ))
        RoutePoint.objects.bulk_create(objs)
        return Response({"status": "ok", "count": len(objs)}, status=status.HTTP_200_OK)

class GameBoardViewSet(viewsets.ModelViewSet):
    """
    /api/boards/        – lista tylko moich plansz
    /api/boards/<id>/   – CRUD na mojej planszy
    """
    serializer_class      = GameBoardSerializer
    authentication_classes = [
        authentication.TokenAuthentication,   # lub JWT
        authentication.SessionAuthentication
    ]
    permission_classes     = [permissions.IsAuthenticated, IsOwner]

    def get_permissions(self):
        if self.action in ("retrieve",):                     # GET /api/boards/<id>/
            return [permissions.AllowAny()]
        if self.action in ("list",):                         # GET /api/boards/
            return [permissions.IsAuthenticated()]
        return [permissions.IsAuthenticated(), IsOwner()]

    def get_queryset(self):
        return GameBoard.objects.all()

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)

class PublicBoardView(RetrieveAPIView):
    """
    /api/public-boards/<id>/   – anon GET
    """
    queryset           = GameBoard.objects.all()
    serializer_class   = GameBoardSerializer
    permission_classes = [AllowAny]