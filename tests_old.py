import tempfile
from django.contrib.auth import get_user_model
from django.test import TestCase, Client
from django.urls import reverse
from rest_framework.test import APITestCase, APIClient
from rest_framework.authtoken.models import Token
from rest_framework import status
from .routes.models import BackgroundImage, Route, RoutePoint

User = get_user_model()

class ModelsTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(username='tester', password='pass')
        cls.bg = BackgroundImage.objects.create(name='TestMap', image=tempfile.NamedTemporaryFile(suffix='.png').name)
        cls.route = Route.objects.create(owner=cls.user, background=cls.bg)
        cls.point = RoutePoint.objects.create(route=cls.route, x=10, y=20, order=1)

    def test_route_relations(self):
        self.assertEqual(self.route.owner, self.user)
        self.assertEqual(self.route.background, self.bg)

    def test_routepoint_relations(self):
        self.assertEqual(self.point.route, self.route)
        self.assertEqual(self.point.x, 10)
        self.assertEqual(self.point.y, 20)
        self.assertEqual(self.point.order, 1)

class WebViewsTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        self.user1 = User.objects.create_user(username='u1', password='pass')
        self.user2 = User.objects.create_user(username='u2', password='pass')
        self.bg = BackgroundImage.objects.create(name='Map', image=tempfile.NamedTemporaryFile(suffix='.png').name)
        self.route1 = Route.objects.create(owner=self.user1, background=self.bg)
        self.route2 = Route.objects.create(owner=self.user2, background=self.bg)

        token1 = Token.objects.create(user=self.user1)

    def test_login_required_redirect(self):
        resp = self.client.get(reverse('route_list'))
        self.assertRedirects(resp, '/accounts/login/?next=/')

    def test_user_can_view_own_route(self):
        self.client.login(username='u1', password='pass')
        resp = self.client.get(reverse('route_detail', args=[self.route1.id]))
        self.assertEqual(resp.status_code, 200)

    def test_user_cannot_view_other_route(self):
        self.client.login(username='u1', password='pass')
        resp = self.client.get(reverse('route_detail', args=[self.route2.id]))
        self.assertIn(resp.status_code, (403, 404))

class APITestRoutes(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='apiuser', password='pass')
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)
        self.bg = BackgroundImage.objects.create(name='Map', image=tempfile.NamedTemporaryFile(suffix='.png').name)
        self.route = Route.objects.create(owner=self.user, background=self.bg)

    def test_create_route(self):
        url = reverse('route-list')
        data = {'background': self.bg.id}
        resp = self.client.post(url, data)
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        self.assertEqual(resp.data['background'], self.bg.id)

    def test_list_routes(self):
        resp = self.client.get(reverse('route-list'))
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertTrue(all(r['id'] == self.route.id for r in resp.data))

class APITestRoutePoints(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='apiuser2', password='pass')
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)
        self.bg = BackgroundImage.objects.create(name='Map2', image=tempfile.NamedTemporaryFile(suffix='.png').name)
        self.route = Route.objects.create(owner=self.user, background=self.bg)

    def test_add_point(self):
        url = reverse('route-point-list', args=[self.route.id])
        data = {'x': 5, 'y': 10}
        resp = self.client.post(url, data)
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        self.assertEqual(resp.data['x'], 5)

    def test_delete_point(self):
        point = RoutePoint.objects.create(route=self.route, x=1, y=2, order=1)
        url = reverse('route-point-detail', args=[self.route.id, point.id])
        resp = self.client.delete(url)
        self.assertEqual(resp.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(RoutePoint.objects.filter(id=point.id).exists())

    def test_unauthenticated_access(self):
        client = APIClient()
        url = reverse('route-point-list', args=[self.route.id])
        resp = client.get(url)
        self.assertIn(resp.status_code, (status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN))
