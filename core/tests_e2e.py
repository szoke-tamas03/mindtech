from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status
from django.db import connection
from django.contrib.auth import get_user_model

User = get_user_model()

from .models import Restaurant, MenuItem

class FoodOrderingE2ETests(APITestCase):
    def setUp(self):
        self.cust_data = {
            "username": "custX", "email": "cx@example.com", "password": "abc123",
            "is_customer": True, "is_restaurant": False
        }
        self.resto_data = {
            "username": "restY", "email": "ry@example.com", "password": "abc123",
            "is_customer": False, "is_restaurant": True
        }
        u1 = self.client.post(reverse('register'), self.cust_data)
        u2 = self.client.post(reverse('register'), self.resto_data)

        connection.close()

        self.assertTrue(User.objects.filter(username="custX").exists(), "User custX not found after register!")
        self.assertTrue(User.objects.filter(username="restY").exists(), "User restY not found after register!")

        # Customer login
        resp_cust = self.client.post(reverse('token_obtain_pair'), {"username": "custX", "password": "abc123"})
        self.assertEqual(resp_cust.status_code, 200, f"Customer login failed: {resp_cust.data}")
        self.assertIn("access", resp_cust.data, f"Customer login response: {resp_cust.data}")
        c_token = resp_cust.data["access"]

        # Resto login
        resp_resto = self.client.post(reverse('token_obtain_pair'), {"username": "restY", "password": "abc123"})
        self.assertEqual(resp_resto.status_code, 200, f"Restaurant login failed: {resp_resto.data}")
        self.assertIn("access", resp_resto.data, f"Restaurant login response: {resp_resto.data}")
        r_token = resp_resto.data["access"]

        self.cust_token, self.resto_token = c_token, r_token
        self.restaurant = Restaurant.objects.create(user=User.objects.get(username="restY"), name="Place2", description="d")
        self.menu_item = MenuItem.objects.create(restaurant=self.restaurant, name="Food2", price=1000)
        self.client.credentials(HTTP_AUTHORIZATION='Bearer ' + self.cust_token)
        order_data = {
            "customerId": u1.data["id"], "restaurantId": self.restaurant.id,
            "items": [{"itemId": self.menu_item.id, "quantity": 1}]
        }
        resp = self.client.post(reverse('order-create'), order_data, format='json')
        self.order_id = resp.data["id"]

    def test_full_ordering_flow(self):
        reg_url = reverse('register')
        cust_data = {
            "username": "custE2E", "email": "custE2E@example.com", "password": "secretcust",
            "is_customer": True, "is_restaurant": False
        }
        cust_reg = self.client.post(reg_url, cust_data)
        cust_id = cust_reg.data["id"]

        connection.close()
        self.assertTrue(User.objects.filter(username="custE2E").exists(), "User custE2E not found after register!")

        login_cust = self.client.post(reverse('token_obtain_pair'), {
            "username": cust_data["username"], "password": cust_data["password"]
        })
        self.assertEqual(login_cust.status_code, 200, f"Customer login failed: {login_cust.data}")
        self.assertIn("access", login_cust.data, f"Customer login response: {login_cust.data}")
        cust_token = login_cust.data["access"]

        self.client.credentials(HTTP_AUTHORIZATION='Bearer ' + cust_token)
        resp = self.client.get(reverse('restaurant-list'))
        self.assertEqual(resp.status_code, 200)
        self.assertTrue(any(r["name"] == "Place2" for r in resp.data))

        menu_resp = self.client.get(reverse('restaurant-menu', kwargs={'pk': self.restaurant.id}))
        self.assertEqual(menu_resp.status_code, 200)
        self.assertTrue(any(item["name"] == "Food2" for item in menu_resp.data))

        order_data = {
            "customerId": cust_id,
            "restaurantId": self.restaurant.id,
            "items": [{"itemId": self.menu_item.id, "quantity": 1, "special_instructions": "well done"}]
        }
        order_resp = self.client.post(reverse('order-create'), order_data, format="json")
        self.assertEqual(order_resp.status_code, 201)
        order_id = order_resp.data["id"]
        self.assertEqual(order_resp.data["status"], "received")

        detail_url = reverse("order-detail", kwargs={"pk": order_id})
        detail_resp = self.client.get(detail_url)
        self.assertEqual(detail_resp.status_code, 200)
        self.assertEqual(detail_resp.data['id'], order_id)

        self.client.credentials(HTTP_AUTHORIZATION='Bearer ' + self.resto_token)
        status_url = reverse("order-status-update", kwargs={"pk": order_id})
        status_resp = self.client.patch(status_url, {"status": "preparing"}, format='json')
        self.assertEqual(status_resp.status_code, 200)
        self.assertEqual(status_resp.data['status'], "preparing")

class FoodOrderingE2EForbiddenTests(APITestCase):
    def setUp(self):
        self.cust_data = {
            "username": "custX", "email": "cx@example.com", "password": "abc123",
            "is_customer": True, "is_restaurant": False
        }
        self.resto_data = {
            "username": "restY", "email": "ry@example.com", "password": "abc123",
            "is_customer": False, "is_restaurant": True
        }
        u1 = self.client.post(reverse('register'), self.cust_data)
        u2 = self.client.post(reverse('register'), self.resto_data)

        connection.close()

        self.assertTrue(User.objects.filter(username="custX").exists(), "User custX not found after register!")
        self.assertTrue(User.objects.filter(username="restY").exists(), "User restY not found after register!")

        resp_cust = self.client.post(reverse('token_obtain_pair'), {"username": "custX", "password": "abc123"})
        self.assertEqual(resp_cust.status_code, 200, f"Customer login failed: {resp_cust.data}")
        self.assertIn("access", resp_cust.data, f"Customer login response: {resp_cust.data}")
        c_token = resp_cust.data["access"]

        resp_resto = self.client.post(reverse('token_obtain_pair'), {"username": "restY", "password": "abc123"})
        self.assertEqual(resp_resto.status_code, 200, f"Restaurant login failed: {resp_resto.data}")
        self.assertIn("access", resp_resto.data, f"Restaurant login response: {resp_resto.data}")
        r_token = resp_resto.data["access"]

        self.cust_token, self.resto_token = c_token, r_token
        self.restaurant = Restaurant.objects.create(user=User.objects.get(username="restY"), name="Place2", description="d")
        self.menu_item = MenuItem.objects.create(restaurant=self.restaurant, name="Food2", price=1000)
        self.client.credentials(HTTP_AUTHORIZATION='Bearer ' + self.cust_token)
        order_data = {
            "customerId": u1.data["id"], "restaurantId": self.restaurant.id,
            "items": [{"itemId": self.menu_item.id, "quantity": 1}]
        }
        resp = self.client.post(reverse('order-create'), order_data, format='json')
        self.order_id = resp.data["id"]

    def test_customer_cannot_patch_status(self):
        self.client.credentials(HTTP_AUTHORIZATION='Bearer ' + self.cust_token)
        resp = self.client.patch(reverse("order-status-update", kwargs={"pk": self.order_id}),
                                 {"status": "preparing"}, format="json")
        self.assertIn(resp.status_code, [403, 405])

    def test_wrong_role_cannot_see_other_orders(self):
        reg2 = self.client.post(reverse('register'), {
            "username": "cust2", "email": "c2@example.com", "password": "abc123",
            "is_customer": True, "is_restaurant": False
        })
        connection.close()
        self.assertTrue(User.objects.filter(username="cust2").exists(), "User cust2 not found after register!")

        resp2 = self.client.post(reverse('token_obtain_pair'), {"username": "cust2", "password": "abc123"})
        self.assertEqual(resp2.status_code, 200, f"Second customer login failed: {resp2.data}")
        self.assertIn("access", resp2.data, f"Second customer login response: {resp2.data}")
        tok2 = resp2.data["access"]
        self.client.credentials(HTTP_AUTHORIZATION='Bearer ' + tok2)
        resp = self.client.get(reverse("order-detail", kwargs={"pk": self.order_id}))
        self.assertEqual(resp.status_code, 403)

class FoodOrderingPublicE2E(APITestCase):
    def test_api_requires_auth(self):
        resp = self.client.get(reverse("restaurant-list"))
        self.assertEqual(resp.status_code, 401)
        resp2 = self.client.post(reverse("order-create"), {})
        self.assertEqual(resp2.status_code, 401)