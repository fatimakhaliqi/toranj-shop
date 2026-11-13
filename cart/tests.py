from django.test import TestCase
from django.urls import reverse

from catalog.tests import make_product
from orders.models import Coupon


class CartTests(TestCase):
    def setUp(self):
        self.p = make_product(stock=3, price=100000)

    def test_add_clamps_to_stock(self):
        self.client.post(reverse("cart:add", args=[self.p.pk]), {"quantity": "10"})
        r = self.client.get(reverse("cart:detail"))
        self.assertEqual(r.context["cart"].data[str(self.p.pk)], 3)

    def test_negative_or_garbage_quantity(self):
        self.client.post(reverse("cart:add", args=[self.p.pk]), {"quantity": "abc"})
        self.client.post(reverse("cart:update", args=[self.p.pk]), {"quantity": "-9"})
        self.assertEqual(self.client.get(reverse("cart:detail")).status_code, 200)

    def test_add_requires_post(self):
        self.assertEqual(self.client.get(reverse("cart:add", args=[self.p.pk])).status_code, 405)

    def test_open_redirect_blocked(self):
        r = self.client.post(reverse("cart:add", args=[self.p.pk]), {"next": "https://evil.example/"})
        self.assertEqual(r["Location"], reverse("cart:detail"))

    def test_coupon(self):
        Coupon.objects.create(code="OFF10", percent=10)
        self.client.post(reverse("cart:add", args=[self.p.pk]))
        self.client.post(reverse("cart:coupon_apply"), {"code": "off10"})
        cart = self.client.get(reverse("cart:detail")).context["cart"]
        self.assertEqual(cart.discount, 10000)
