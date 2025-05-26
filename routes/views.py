from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm
from django.db import IntegrityError, transaction
from django.shortcuts import get_object_or_404, redirect, render
from .forms import RouteCreateForm, PointForm, BoardForm
from .models import Route, RoutePoint, GameBoard

PALETTE = [
    "#ef4444", "#f97316", "#eab308", "#22c55e", "#14b8a6",
    "#0ea5e9", "#6366f1", "#8b5cf6", "#ec4899", "#f43f5e",
]

@login_required
def point_add(request, pk):
    route = get_object_or_404(Route, pk=pk, owner=request.user)
    form = PointForm(request.POST)
    if form.is_valid():
        point = form.save(commit=False)
        point.route = route
        point.order = route.points.count() + 1
        point.save()
    return redirect("route_detail", pk)

@login_required
def point_delete(request, pk, point_id):
    route = get_object_or_404(Route, pk=pk, owner=request.user)
    RoutePoint.objects.filter(pk=point_id, route=route).delete()
    return redirect("route_detail", pk)

@login_required
def board_list_mine(request):
    boards = GameBoard.objects.filter(owner=request.user)
    # Pobierz trasy użytkownika do wszystkich plansz
    user_routes = {r.background_id: r for r in Route.objects.filter(owner=request.user)}
    for b in boards:
        # Przypisz trasę użytkownika do planszy lub None
        b.route_for_user = user_routes.get(b.id, None)
    return render(request, "routes/board_list.html",
                  {"boards": boards, "mine": True})

def board_list_all(request):
    boards = GameBoard.objects.select_related("owner").all()
    user = request.user if request.user.is_authenticated else None
    if user:
        user_routes = {r.background_id: r for r in Route.objects.filter(owner=user)}
        for b in boards:
            b.route_for_user = user_routes.get(b.id)
    else:
        for b in boards:
            b.route_for_user = None
    return render(request, "routes/board_list.html",
                  {"boards": boards, "user": request.user})

def board_view(request, pk):
    board = get_object_or_404(GameBoard, pk=pk)
    return render(request, "routes/board_view.html", {"board": board})

@login_required
def board_edit(request, pk=None):
    board = None
    if pk:
        board = get_object_or_404(GameBoard, pk=pk, owner=request.user)

    if request.method == "POST":
        form = BoardForm(request.POST, instance=board)
        if form.is_valid():
            board = form.save(commit=False)
            board.owner = request.user
            board.save()
            return redirect("board_edit", pk=board.pk)
    else:
        form = BoardForm(instance=board)

    return render(
        request,
        "routes/board_edit.html",
        {"form": form, "board": board},
    )


@login_required
def route_list(request):
    routes = request.user.routes.select_related("background")
    return render(request, "routes/route_list.html", {"routes": routes})

@login_required
def route_create(request):
    if request.method == "POST":
        form = RouteCreateForm(request.POST)
        if form.is_valid():
            route = form.save(commit=False)
            route.owner = request.user
            route.save()
            return redirect("route_detail", route.pk)
    else:
        form = RouteCreateForm()
    return render(request, "routes/route_form.html", {"form": form})

@login_required
def route_edit(request, pk: int):
    """
    GET /boards/<pk>/route
    • Tworzy (jeśli trzeba) trasę bieżącego usera dla planszy <pk>.
    • Renderuje szablon edytora z obiektami `board` i `route`.
    """
    board = get_object_or_404(GameBoard, pk=pk)

    # --- Jeden-użytkownik-jedna-trasa ---
    try:
        route = Route.objects.get(owner=request.user, background=board)
    except Route.DoesNotExist:
        with transaction.atomic():
            try:
                route, _ = Route.objects.get_or_create(
                    owner=request.user,
                    background=board,
                    defaults={"name": f"Trasa – {board.title}"}
                )
            except IntegrityError:
                # wyścig? – pobierz to, co wstawiła inna transakcja
                route = Route.objects.get(owner=request.user, background=board)

    # --- Edytor (ten sam html i js co wcześniej) ---
    return render(
        request,
        "routes/route_edit.html",      # ← nie zmieniamy szablonu
        {"board": board, "route": route},
    )

@login_required
def route_detail(request, pk):
    route = get_object_or_404(Route, pk=pk, owner=request.user)
    point_form = PointForm()

    points = list(
        route.points.order_by("order").values("id", "x", "y")
    )

    return render(
        request,
        "routes/route_detail.html",
        {"route": route, "points": points, "point_form": point_form},
    )


def register(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            return redirect('login')  # lub inny widok po rejestracji
    else:
        form = UserCreationForm()
    return render(request, 'registration/register.html', {'form': form})