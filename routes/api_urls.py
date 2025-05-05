from django.urls import path, include
from rest_framework_nested import routers
from .api_views import RouteViewSet, RoutePointViewSet
from rest_framework.authtoken.views import obtain_auth_token

router = routers.SimpleRouter()
router.register(r"routes", RouteViewSet, basename="route")

points_router = routers.NestedSimpleRouter(router, r"routes", lookup="route")
points_router.register(r"points", RoutePointViewSet, basename="route-point")

urlpatterns = [
    path("token/", obtain_auth_token, name="api_token"),
    path("", include(router.urls)),
    path("", include(points_router.urls)),
]
