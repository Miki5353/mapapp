from rest_framework import serializers
from .models import Route, RoutePoint

class RoutePointSerializer(serializers.ModelSerializer):
    class Meta:
        model = RoutePoint
        fields = ["id", "order", "x", "y"]

class RouteSerializer(serializers.ModelSerializer):
    points = RoutePointSerializer(many=True, read_only=True)

    class Meta:
        model = Route
        fields = ["id", "background", "created", "points"]
        read_only_fields = ["created"]
