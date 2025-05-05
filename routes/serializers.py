from rest_framework import serializers
from .models import Route, RoutePoint

class RouteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Route
        fields = ["id", "name", "background", "created"]
        read_only_fields = ["id", "created"]

class RoutePointSerializer(serializers.ModelSerializer):
    class Meta:
        model = RoutePoint
        fields = ["id", "x", "y", "order"]
        read_only_fields = ["id", "order"]