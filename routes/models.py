from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _

class GameBoard(models.Model):
    """
    Plansza do gry „Połącz Kropki”.
    dots = [
        {"row": 0, "col": 2, "color": "#ff0000"},
        {"row": 3, "col": 5, "color": "#ff0000"},
        ...
    ]
    """
    owner  = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name="boards",
        on_delete=models.CASCADE
    )

    title  = models.CharField(_("Nazwa planszy"), max_length=50)
    rows   = models.PositiveSmallIntegerField(_("Wiersze"), default=5)
    cols   = models.PositiveSmallIntegerField(_("Kolumny"), default=5)
    dots   = models.JSONField(_("Kropki"), default=list, blank=True)

    created   = models.DateTimeField(auto_now_add=True)
    modified  = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-modified"]

    def __str__(self) -> str:
        return f"Board #{self.pk} ({self.owner})"


class Route(models.Model):
    name = models.CharField(max_length=25)
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="routes"
    )
    background = models.ForeignKey(
        GameBoard, on_delete=models.CASCADE, related_name="routes"
    )
    created = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["background"],
                name="unique_route_per_user_board"
            )
        ]


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
