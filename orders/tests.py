from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from django.urls import reverse

from catalog.tests import make_product
from payments.models import Payment

from .models import Coupon, Order
from .services import expire_unpaid_orders

User = get_user_model()
PW = "Str0ng-Pass-12345"
ADDR = {"full_name": "علی رضایی", "phone": "۰۹۱۲۱۲۳۴۵۶۷", "province": "تهران", "city": "تهران",
        "postal_code": "۱۲۳۴۵۶۷۸۹۰", "address": "خیابان آزادی، پلاک ۱"}


@override_settings(DEBUG=True, ZARINPAL_MERCHANT_ID="")
class FlowTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user("ali", "ali@example.com", PW)
        self.p = make_product(stock=5, price=100000)
        self.client.login(username="ali", password=PW)
        self.client.post(reverse("cart:add", args=[self.p.pk]), {"quantity": "2"})

    def checkout(self):
        return self.client.post(reverse("orders:checkout"), ADDR)

    def test_checkout_reserves_stock_and_prices_server_side(self):
        self.assertEqual(self.checkout().status_code, 302)
        order = Order.objects.get()
        self.assertEqual(order.subtotal, 200000)
        self.assertEqual(order.shipping, 40000)
        self.assertEqual(order.total, 240000)
        self.assertEqual(order.phone, "09121234567")
        self.p.refresh_from_db()
        self.assertEqual(self.p.stock, 3)

    def test_invalid_phone_rejected(self):
        r = self.client.post(reverse("orders:checkout"), {**ADDR, "phone": "123"})
        self.assertEqual(r.status_code, 200)
        self.assertEqual(Order.objects.count(), 0)

    def test_coupon_applied_and_counted(self):
        Coupon.objects.create(code="OFF10", percent=10)
        self.client.post(reverse("cart:coupon_apply"), {"code": "OFF10"})
        self.checkout()
        order = Order.objects.get()
        self.assertEqual(order.discount, 20000)
        self.assertEqual(Coupon.objects.get().used_count, 1)

    def test_cancel_restores_stock(self):
        self.checkout()
        order = Order.objects.get()
        self.client.post(reverse("orders:cancel", args=[order.code]))
        self.p.refresh_from_db()
        order.refresh_from_db()
        self.assertEqual(self.p.stock, 5)
        self.assertEqual(order.status, Order.Status.CANCELLED)

    def test_idor_other_user_cannot_see_or_pay(self):
        self.checkout()
        order = Order.objects.get()
        User.objects.create_user("eve", "eve@example.com", PW)
        self.client.login(username="eve", password=PW)
        self.assertEqual(self.client.get(order.get_absolute_url()).status_code, 404)
        self.assertEqual(self.client.post(reverse("payments:start", args=[order.code])).status_code, 404)

    def test_successful_payment_via_mock_gateway(self):
        self.checkout()
        order = Order.objects.get()
        r = self.client.post(reverse("payments:start", args=[order.code]))
        self.assertEqual(r.status_code, 302)
        pay = Payment.objects.get()
        self.assertEqual(pay.amount, order.total)
        self.client.get(reverse("payments:callback"), {"Authority": pay.authority, "Status": "OK"})
        order.refresh_from_db()
        pay.refresh_from_db()
        self.assertEqual(order.status, Order.Status.PAID)
        self.assertEqual(pay.status, Payment.Status.SUCCESS)
        self.p.refresh_from_db()
        self.assertEqual(self.p.sold_count, 2)
        # تکرار callback نباید دوباره چیزی را تغییر دهد (idempotent)
        self.client.get(reverse("payments:callback"), {"Authority": pay.authority, "Status": "OK"})
        self.p.refresh_from_db()
        self.assertEqual(self.p.sold_count, 2)

    def test_failed_payment_keeps_order_pending(self):
        self.checkout()
        order = Order.objects.get()
        self.client.post(reverse("payments:start", args=[order.code]))
        pay = Payment.objects.get()
        self.client.get(reverse("payments:callback"), {"Authority": pay.authority, "Status": "NOK"})
        order.refresh_from_db()
        self.assertEqual(order.status, Order.Status.PENDING)

    def test_cannot_forge_success_for_cancelled_order(self):
        self.checkout()
        order = Order.objects.get()
        self.client.post(reverse("payments:start", args=[order.code]))
        pay = Payment.objects.get()
        self.client.post(reverse("orders:cancel", args=[order.code]))
        self.client.get(reverse("payments:callback"), {"Authority": pay.authority, "Status": "OK"})
        order.refresh_from_db()
        self.assertEqual(order.status, Order.Status.CANCELLED)

    def test_expire_unpaid(self):
        from datetime import timedelta
        from django.utils import timezone
        self.checkout()
        Order.objects.update(created_at=timezone.now() - timedelta(hours=2))
        self.assertEqual(expire_unpaid_orders(), 1)
        self.p.refresh_from_db()
        self.assertEqual(self.p.stock, 5)

    def test_mock_gateway_hidden_in_production(self):
        self.checkout()
        order = Order.objects.get()
        self.client.post(reverse("payments:start", args=[order.code]))
        pay = Payment.objects.get()
        with override_settings(DEBUG=False):
            self.assertEqual(self.client.get(reverse("payments:mock", args=[pay.authority])).status_code, 404)
