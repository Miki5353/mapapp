from django.conf import settings
from django.db import models

class BackgroundImage(models.Model):
    name = models.CharField(max_length=100)
    title = models.CharField(max_length=50)
    image = models.ImageField(upload_to="backgrounds/")

    def __str__(self) -> str:
        return self.title


class Route(models.Model):
    name = models.CharField(max_length=20)
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="routes"
    )
    background = models.ForeignKey(
        BackgroundImage, on_delete=models.PROTECT, related_name="routes"
    )
    created = models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:
        return f"Route #{self.pk} ({self.owner})"


class RoutePoint(models.Model):
    route = models.ForeignKey(
        Route, on_delete=models.CASCADE, related_name="points"
    )
    order = models.PositiveIntegerField()
    x = models.PositiveIntegerField()
    y = models.PositiveIntegerField()

    class Meta:
        unique_together = ("route", "order")
        ordering = ["order"]

    def __str__(self) -> str:
        return f"P{self.order}@({self.x}, {self.y})"
