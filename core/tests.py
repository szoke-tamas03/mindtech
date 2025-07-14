from django.urls import reverse
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from .models import User, Restaurant, MenuItem, Order, OrderItem

class JWTApiTests(APITestCase):

    def setUp(self):

        self.customer_credentials = {
            "username": "customer1",
            "email": "cust1@test.hu",
            "password": "valamititkos",
            "is_customer": True,
            "is_restaurant": False
        }
        self.customer = self.register_and_get_user(self.customer_credentials)
        self.customer_token = self.login_and_get_token(self.customer_credentials["username"], self.customer_credentials["password"])


        self.restaurant_credentials = {
            "username": "restaurant1",
            "email": "restaurant1@test.hu",
            "password": "nagyonbiztos",
            "is_customer": False,
            "is_restaurant": True
        }
        self.restaurant = self.register_and_get_user(self.restaurant_credentials)
        self.restaurant_token = self.login_and_get_token(self.restaurant_credentials["username"], self.restaurant_credentials["password"])


        self.customer2 = self.register_and_get_user({
            "username": "customer2",
            "email": "cust2@test.hu",
            "password": "pass2pass2",
            "is_customer": True,
            "is_restaurant": False
        })
        self.customer2_token = self.login_and_get_token("customer2", "pass2pass2")

        self.restaurant2 = self.register_and_get_user({
            "username": "restaurant2",
            "email": "restaurant2@test.hu",
            "password": "masikpasss",
            "is_customer": False,
            "is_restaurant": True
        })
        self.restaurant2_token = self.login_and_get_token("restaurant2", "masikpasss")


        self.restaurant = Restaurant.objects.create(user=self.restaurant, name="test restaurant", description="Valami leiras")
        self.menuitem1 = MenuItem.objects.create(restaurant=self.restaurant, name="Pizza", price=2200, description="Sonkás pizza")
        self.menuitem2 = MenuItem.objects.create(restaurant=self.restaurant, name="soup", price=1000, description="Hússoup")

        self.restaurant2 = Restaurant.objects.create(user=self.restaurant2, name="other restaurant", description="other leiras")
        self.menuitem3 = MenuItem.objects.create(restaurant=self.restaurant2, name="Sushi", price=3900, description="Makizushi")


        self.order = Order.objects.create(customer=self.customer, restaurant=self.restaurant, status='received')
        self.orderitem = OrderItem.objects.create(order=self.order, menu_item=self.menuitem1, quantity=1, special_instructions="csípös")

    def get_auth_client(self, token):
        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION="Bearer " + token)
        return client

    def register_and_get_user(self, data):
        reg_url = reverse('register')
        resp = self.client.post(reg_url, data, format='json')
        return User.objects.get(username=data["username"])

    def login_and_get_token(self, username, password):
        login_url = reverse('token_obtain_pair')
        resp = self.client.post(login_url, {"username": username, "password": password}, format='json')
        return resp.data["access"]


    def test_register_and_login_token(self):
        data = {"username": "demo", "email": "demo@test.hu", "password": "titokos", "is_customer": True, "is_restaurant": False}
        url = reverse("register")
        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, 201)
        login_resp = self.client.post(reverse("token_obtain_pair"), {"username":"demo","password":"titokos"})
        self.assertEqual(login_resp.status_code, 200)
        self.assertIn("access", login_resp.data)

    def test_register_bad_role(self):
        reg_url = reverse("register")
        data = {"username": "rossz", "email": "bad@something.com", "password": "abcdef", "is_customer": True, "is_restaurant": True}
        resp = self.client.post(reg_url, data, format='json')
        self.assertEqual(resp.status_code, 400)
        self.assertIn("non_field_errors", resp.data)

    def test_login_bad_password(self):
        login_url = reverse("token_obtain_pair")
        resp = self.client.post(login_url, {"username":"customer1", "password":"rossz"})
        self.assertEqual(resp.status_code, 401)
        self.assertIn("No active account found", str(resp.data))


    def test_restaurant_list_requires_jwt(self):
        url = reverse("restaurant-list")
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 401)
        client = self.get_auth_client(self.customer_token)
        resp2 = client.get(url)
        self.assertEqual(resp2.status_code, 200)
        self.assertTrue(any(r["name"] == "test restaurant" for r in resp2.data))

    def test_menu_list_of_restaurant(self):
        url = reverse("restaurant-menu", kwargs={"pk": self.restaurant.id})
        client = self.get_auth_client(self.customer_token)
        resp = client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assertTrue(any(item["name"] == "Pizza" for item in resp.data))


    def test_customer_create_order_own_and_only_authenticated(self):
        url = reverse("order-create")
        data = {
            "customerId": self.customer.id,
            "restaurantId": self.restaurant.id,
            "items": [
                {"itemId": self.menuitem2.id, "quantity":2, "special_instructions": "sok borssal"}
            ]
        }
        resp = self.client.post(url, data, format='json')
        self.assertEqual(resp.status_code, 401)
        client = self.get_auth_client(self.customer_token)
        resp2 = client.post(url, data, format='json')
        self.assertEqual(resp2.status_code, 201)
        data_idegen = dict(data)
        data_idegen["customerId"] = self.customer2.id
        resp3 = client.post(url, data_idegen, format='json')
        self.assertEqual(resp3.status_code, 403)

    def test_order_for_nonexistent_menuitem(self):
        url = reverse("order-create")
        client = self.get_auth_client(self.customer_token)
        data = {
            "customerId": self.customer.id,
            "restaurantId": self.restaurant.id,
            "items": [
                {"itemId": 9999, "quantity": 1}
            ]
        }
        resp = client.post(url, data, format="json")
        self.assertEqual(resp.status_code, 400)
        self.assertIn("error", resp.data)


    def test_customer_can_get_own_order_detail_but_not_other(self):
        url = reverse("order-detail", kwargs={"pk": self.order.id})
        client = self.get_auth_client(self.customer_token)
        resp = client.get(url)
        self.assertEqual(resp.status_code, 200)
        client2 = self.get_auth_client(self.customer2_token)
        resp2 = client2.get(url)
        self.assertEqual(resp2.status_code, 403)

    def test_restaurant_can_see_own_orders_list_but_not_others(self):
        url = reverse("restaurant-orders") + f"?restaurantId={self.restaurant.id}"
        client = self.get_auth_client(self.restaurant_token)
        resp = client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assertTrue(any(r["id"] == self.order.id for r in resp.data))
        client2 = self.get_auth_client(self.restaurant2_token)
        resp2 = client2.get(url)
        self.assertEqual(resp2.status_code, 200)
        self.assertFalse(any(r["id"] == self.order.id for r in resp2.data))


    def test_customer_cannot_status_update(self):
        url = reverse("order-status-update", kwargs={"pk": self.order.id})
        client = self.get_auth_client(self.customer_token)
        resp = client.patch(url, {"status": "delivered"}, format='json')
        self.assertEqual(resp.status_code, 403)

    def test_restaurant_can_status_update_only_own_order_and_valid_status(self):
        url = reverse("order-status-update", kwargs={"pk": self.order.id})
        client = self.get_auth_client(self.restaurant_token)
        resp = client.patch(url, {"status": "preparing"}, format='json')
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.data["status"], "preparing")
        resp2 = client.patch(url, {"status": "idegen"}, format='json')
        self.assertEqual(resp2.status_code, 400)
        client2 = self.get_auth_client(self.restaurant2_token)
        resp3 = client2.patch(url, {"status": "ready"}, format='json')
        self.assertEqual(resp3.status_code, 403)

    def test_order_create_with_empty_items(self):
        url = reverse("order-create")
        client = self.get_auth_client(self.customer_token)
        data = {
            "customerId": self.customer.id,
            "restaurantId": self.restaurant.id,
            "items": []
        }
        resp = client.post(url, data, format='json')
        self.assertEqual(resp.status_code, 400)
        self.assertIn("error", resp.data)

    def test_order_detail_auth_required(self):
        url = reverse("order-detail", kwargs={"pk": self.order.id})
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 401)

    def test_long_special_instructions_ok(self):
        url = reverse("order-create")
        client = self.get_auth_client(self.customer_token)
        long_text = "x" * 2048
        data = {
            "customerId": self.customer.id,
            "restaurantId": self.restaurant.id,
            "items": [
                {"itemId": self.menuitem1.id, "quantity": 1, "special_instructions": long_text}
            ]
        }
        resp = client.post(url, data, format='json')
        self.assertEqual(resp.status_code, 201)
        self.assertEqual(resp.data["items"][0]["special_instructions"], long_text)