from rest_framework import serializers
from .models import Route, RoutePoint, GameBoard


class RoutePointSerializer(serializers.ModelSerializer):
    class Meta:
        model = RoutePoint
        fields = ["id", "order", "x", "y"]
        read_only_fields = ["id", "order"]

class RouteSerializer(serializers.ModelSerializer):
    points = RoutePointSerializer(many=True, read_only=True)

    class Meta:
        model = Route
        fields = ["id", "name", "background", "created", "points"]
        read_only_fields = ["id", "created"]


class GameBoardSerializer(serializers.ModelSerializer):
    class Meta:
        model  = GameBoard
        fields = ["id", "title", "rows", "cols", "dots", "created", "modified"]
        read_only_fields = ["id", "created", "modified", "owner"]

    def validate(self, data):
        """
        • każdy kolor dokładnie 2×
        • kropki mieszczą się w siatce
        • brak duplikatów pól (row, col)
        """
        rows = data.get("rows", getattr(self.instance, "rows", None))
        cols = data.get("cols", getattr(self.instance, "cols", None))
        dots = data.get("dots", [])

        if rows is None or cols is None:
            raise serializers.ValidationError("Nie podano wymiarów planszy.")

        # 1. koordynaty w zakresie i unikalność pól
        seen = set()
        for d in dots:
            r, c = d["row"], d["col"]
            if not (0 <= r < rows and 0 <= c < cols):
                raise serializers.ValidationError("Kropka poza zakresem planszy.")
            if (r, c) in seen:
                raise serializers.ValidationError("Podwójna kropka w tej samej komórce.")
            seen.add((r, c))

        # 2. każdy kolor dokładnie 2×
        from collections import Counter
        counts = Counter(d["color"] for d in dots)
        wrong  = [col for col, n in counts.items() if n != 2]
        if wrong:
            raise serializers.ValidationError(
                f"Kolory {', '.join(wrong)} występują nie dokładnie 2 razy."
            )

        return data