from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.db.models.deletion import ProtectedError
from django.test import TestCase, Client
from django.urls import reverse


from rest_framework.test import APIClient, APITestCase
from rest_framework.authtoken.models import Token
from rest_framework import status

from .models import BackgroundImage, Route, RoutePoint  # adjust import path

User = get_user_model()


###############################################################################
# Helper mixins & utilities
###############################################################################


def create_image(name: str = "map.png", size: tuple[int, int] = (10, 10)) -> SimpleUploadedFile:
    """Return an in‑memory 1‑pixel PNG so we do not rely on fixture files."""
    from io import BytesIO
    from PIL import Image

    image_io = BytesIO()
    img = Image.new("RGB", size, color="red")
    img.save(image_io, format="PNG")
    image_io.seek(0)
    return SimpleUploadedFile(name, image_io.read(), content_type="image/png")


class AuthenticatedAPIMixin:
    """Mixin that creates a user + token and exposes an authenticated APIClient."""

    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user("alice", password="secret123")
        cls.token = Token.objects.create(user=cls.user)
        cls.api_client = APIClient()
        cls.api_client.credentials(HTTP_AUTHORIZATION=f"Token {cls.token.key}")

        cls.other_user = User.objects.create_user("bob", password="secret123")
        cls.other_token = Token.objects.create(user=cls.other_user)

###############################################################################
# 1. Model tests
###############################################################################


class BackgroundImageModelTest(TestCase):
    def test_create_background_image(self):
        bg = BackgroundImage.objects.create(title="Test plan", image=create_image())
        self.assertEqual(str(bg), "Test plan")
        self.assertTrue(bg.image.name.endswith(".png"))


class RouteModelTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user("foo", password="bar")
        cls.bg = BackgroundImage.objects.create(title="BG", image=create_image("bg.png"))

    def test_route_fields_and_str(self):
        route = Route.objects.create(name="Route 1", owner=self.user, background=self.bg)
        self.assertEqual(route.name, "Route 1")
        self.assertEqual(route.owner, self.user)
        self.assertEqual(route.background, self.bg)
        self.assertEqual(str(route), "Route #1 (foo)")

    def test_background_protect_on_delete(self):
        route = Route.objects.create(name="Route 1", owner=self.user, background=self.bg)
        with self.assertRaises(ProtectedError):
            self.bg.delete()

    def test_route_and_points_relationship(self):
        route = Route.objects.create(name="Route 1", owner=self.user, background=self.bg)
        p1 = RoutePoint.objects.create(route=route, order=1, x=10, y=20)
        p2 = RoutePoint.objects.create(route=route, order=2, x=30, y=40)

        # Backward FK relation
        self.assertEqual(route.points.count(), 2)
        self.assertIn(p1, route.points.all())
        self.assertEqual(p2.order, 2)

        # Cascade delete of points when route is deleted
        route.delete()
        self.assertFalse(RoutePoint.objects.filter(pk=p1.pk).exists())


class RoutePointModelTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user("foo", password="bar")
        cls.bg = BackgroundImage.objects.create(title="BG", image=create_image("bg.png"))
        cls.route = Route.objects.create(name="Route X", owner=cls.user, background=cls.bg)

    def test_create_route_point(self):
        pt = RoutePoint.objects.create(route=self.route, order=5, x=1.23, y=4.56)
        self.assertEqual(pt.route, self.route)
        self.assertEqual(pt.order, 5)
        self.assertEqual(pt.x, 1.23)
        self.assertEqual(pt.y, 4.56)
        self.assertEqual(
            str(pt), f"P{5}@({1.23}, {4.56})"
        )

    def test_ordering_of_points(self):
        p1 = RoutePoint.objects.create(route=self.route, order=2, x=0, y=0)
        p2 = RoutePoint.objects.create(route=self.route, order=1, x=1, y=1)
        points = list(RoutePoint.objects.filter(route=self.route))
        self.assertEqual(points, [p2, p1])

###############################################################################
# 2. Web (HTML) view tests – authentication & CRUD
###############################################################################


class RouteViewTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user("viewer", password="pass")
        cls.bg = BackgroundImage.objects.create(title="BG", image=create_image())

    def setUp(self):
        self.client = Client()

    def test_requires_login(self):
        url = reverse("route_list")  # adjust as per your urls.py
        response = self.client.get(url)
        self.assertRedirects(
            response, f"{reverse('login')}?next={url}", fetch_redirect_response=False
        )

    def test_owner_sees_only_their_routes(self):
        other_user = User.objects.create_user("someone", password="123")
        Route.objects.create(name="not‑mine", owner=other_user, background=self.bg)
        Route.objects.create(name="mine", owner=self.user, background=self.bg)

        self.client.login(username="viewer", password="pass")
        response = self.client.get(reverse("route_list"))
        self.assertContains(response, "mine")
        self.assertNotContains(response, "not‑mine")

    def test_create_route_and_add_point_via_form(self):
        self.client.login(username="viewer", password="pass")

        # Create route
        create_url = reverse("route_create")
        resp = self.client.post(create_url, {"name": "Lab", "background": self.bg.id})
        self.assertRedirects(resp, reverse("route_detail", args=[1]))

        # Add a point
        add_pt_url = reverse("point_add", args=[1])
        resp = self.client.post(add_pt_url, {"x": 5, "y": 10})
        self.assertEqual(resp.status_code, 302)  # redirect after success
        self.assertEqual(RoutePoint.objects.count(), 1)

###############################################################################
# 3. REST‑API tests – authentication & authorisation
###############################################################################


class RouteAPITests(AuthenticatedAPIMixin, APITestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.bg = BackgroundImage.objects.create(title="BG", image=create_image())

    def test_cannot_access_without_token(self):
        res = self.client.get("/api/routes/")  # unauthenticated client
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_create_and_list_routes(self):
        # POST new route
        response = self.api_client.post(
            "/api/routes/",
            {"name": "My API route", "background": self.bg.id},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        route_id = response.data["id"]

        # GET list only my routes
        response = self.api_client.get("/api/routes/")
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["id"], route_id)

        # Other user’s list is empty
        other_client = APIClient()
        other_client.credentials(HTTP_AUTHORIZATION=f"Token {self.other_token.key}")
        res = other_client.get("/api/routes/")
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, [])

    def test_route_detail_and_delete(self):
        route = Route.objects.create(name="to‑delete", owner=self.user, background=self.bg)
        url = f"/api/routes/{route.id}/"

        # Detail
        res = self.api_client.get(url)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data["name"], "to‑delete")

        # Delete
        res = self.api_client.delete(url)
        self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Route.objects.filter(pk=route.id).exists())

    def test_cannot_delete_others_route(self):
        route = Route.objects.create(name="foreign", owner=self.other_user, background=self.bg)
        res = self.api_client.delete(f"/api/routes/{route.id}/")
        self.assertEqual(res.status_code, status.HTTP_404_NOT_FOUND)  # or 403 depending implementation


class RoutePointAPITests(AuthenticatedAPIMixin, APITestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.bg = BackgroundImage.objects.create(title="BG", image=create_image())
        cls.route = Route.objects.create(name="R", owner=cls.user, background=cls.bg)

    def test_add_list_and_delete_point(self):
        add_url = f"/api/routes/{self.route.id}/points/"
        # Add
        res = self.api_client.post(add_url, {"x": 1, "y": 2, "order": 1}, format="json")
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        pt_id = res.data["id"]

        # List
        res = self.api_client.get(add_url)
        self.assertEqual(len(res.data), 1)

        # Delete
        del_url = f"{add_url}{pt_id}/"
        res = self.api_client.delete(del_url)
        self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(RoutePoint.objects.filter(pk=pt_id).exists())

    def test_validation_rejects_missing_fields(self):
        res = self.api_client.post(
            f"/api/routes/{self.route.id}/points/", {"x": 5}, format="json"  # y missing
        )
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("y", res.data)

    def test_forbidden_on_foreign_route(self):
        foreign_route = Route.objects.create(
            name="F", owner=self.other_user, background=self.bg
        )
        res = self.api_client.get(f"/api/routes/{foreign_route.id}/points/")
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)