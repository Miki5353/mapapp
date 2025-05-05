from django.urls import path
from . import views

urlpatterns = [
    path("", views.route_list, name="route_list"),
    path("route/new/", views.route_create, name="route_create"),
    path("route/<int:pk>/", views.route_detail, name="route_detail"),
    path("route/<int:pk>/add/", views.point_add, name="point_add"),
    path("route/<int:pk>/del/<int:point_id>/", views.point_delete, name="point_delete"),
    path('accounts/register/', views.register, name='register')
]
