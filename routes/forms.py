from django import forms
from .models import RoutePoint, Route, GameBoard

class RouteCreateForm(forms.ModelForm):
    class Meta:
        model = Route
        fields = ["name", "background"]

class PointForm(forms.ModelForm):
    class Meta:
        model = RoutePoint
        fields = ["x", "y"]

class BoardForm(forms.ModelForm):
    class Meta:
        model  = GameBoard
        fields = ["title", "rows", "cols"]
        widgets = {
            "rows": forms.NumberInput(attrs={"min": 2, "max": 12}),
            "cols": forms.NumberInput(attrs={"min": 2, "max": 12}),
        }