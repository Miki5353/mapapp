from django import forms
from .models import RoutePoint, Route

class RouteCreateForm(forms.ModelForm):
    class Meta:
        model = Route
        fields = ["name", "background"]

class PointForm(forms.ModelForm):
    class Meta:
        model = RoutePoint
        fields = ["x", "y"]