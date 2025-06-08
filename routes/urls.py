# routes/urls.py
from django.urls import path
from . import views
from .sse import event_stream
from django.views.generic import RedirectView

urlpatterns = [
    path('accounts/register/', views.register, name='register'),

    path("", RedirectView.as_view(url="/boards/", permanent=False)),
    # path("route/new/", views.route_create, name="route_create"),
    # path("route/<int:pk>/", views.route_detail, name="route_detail"),
    # path("route/<int:pk>/add/", views.point_add, name="point_add"),
    # path("route/<int:pk>/del/<int:point_id>/", views.point_delete, name="point_delete"),

    # path("routes/new", views.route_edit, name='route_new'),
    # path("routes/<int:pk>/edit", views.route_edit, name='route_edit'),

    path("boards/", views.board_list_all, name="board_list_all"),
    path("boards/my", views.board_list_mine, name="board_list_mine"),
    path("boards/new", views.board_edit, name="board_new"),
    path("boards/<int:pk>", views.board_view, name="board_view"),
    path("boards/<int:pk>/edit", views.board_edit, name="board_edit"),

    path("boards/<int:pk>/route", views.route_edit, name="route_edit"),
    path("boards/<int:pk>/new", views.route_edit, name="route_new"),

    path("sse/notifications/", event_stream, name="sse_notifications"),
]
