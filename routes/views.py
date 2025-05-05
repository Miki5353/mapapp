from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm
from django.shortcuts import get_object_or_404, redirect, render
from .forms import RouteCreateForm, PointForm
from .models import Route, RoutePoint

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



def register(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            return redirect('login')  # lub inny widok po rejestracji
    else:
        form = UserCreationForm()
    return render(request, 'registration/register.html', {'form': form})