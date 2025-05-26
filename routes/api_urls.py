from django.urls import path
from rest_framework_nested import routers
from .api_views import RouteViewSet, RoutePointViewSet, GameBoardViewSet, PublicBoardView, RoutePointBulkView
from rest_framework.authtoken.views import obtain_auth_token
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

router = routers.DefaultRouter()
router.register("routes", RouteViewSet, basename="route")
router.register("boards", GameBoardViewSet, basename="board")

points_router = routers.NestedSimpleRouter(router, "routes", lookup="route")
points_router.register("points", RoutePointViewSet, basename="route-point")

urlpatterns = [
    path("token/", obtain_auth_token, name="api_token"),
    path("schema/", SpectacularAPIView.as_view(), name="schema"),
    path("docs/",  SpectacularSwaggerView.as_view(url_name="schema"), name="swagger-ui"),
    path("public-boards/<int:pk>/", PublicBoardView.as_view(), name="public-board"),
    path("routes/<int:route_pk>/points/bulk/", RoutePointBulkView.as_view(), name="route-point-bulk"),
    *router.urls,
    *points_router.urls,
]