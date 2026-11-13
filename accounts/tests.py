from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.test import TestCase, override_settings
from django.urls import reverse

User = get_user_model()
PW = "Str0ng-Pass-12345"


class AuthTests(TestCase):
    def setUp(self):
        cache.clear()
        self.user = User.objects.create_user("ali", "ali@example.com", PW)

    def test_register_and_duplicate_email(self):
        data = {"username": "sara", "email": "sara@example.com", "phone": "۰۹۱۲۱۲۳۴۵۶۷",
                "password1": "Another-Str0ng-99", "password2": "Another-Str0ng-99"}
        self.assertEqual(self.client.post(reverse("accounts:register"), data).status_code, 302)
        self.assertEqual(User.objects.get(username="sara").phone, "09121234567")
        self.client.logout()
        data.update(username="other", email="SARA@example.com")
        self.assertEqual(self.client.post(reverse("accounts:register"), data).status_code, 200)

    def test_login_by_email(self):
        r = self.client.post(reverse("accounts:login"), {"username": "ALI@example.com", "password": PW})
        self.assertEqual(r.status_code, 302)

    @override_settings(LOGIN_MAX_ATTEMPTS=3)
    def test_lockout(self):
        for _ in range(3):
            self.client.post(reverse("accounts:login"), {"username": "ali", "password": "bad"})
        self.client.post(reverse("accounts:login"), {"username": "ali", "password": PW})
        self.assertNotIn("_auth_user_id", self.client.session)

    def test_logout_post_only(self):
        self.client.login(username="ali", password=PW)
        self.assertEqual(self.client.get(reverse("accounts:logout")).status_code, 405)
        self.client.post(reverse("accounts:logout"))
        self.assertNotIn("_auth_user_id", self.client.session)

    def test_login_required_pages(self):
        for name in ("accounts:dashboard", "orders:list", "orders:checkout", "catalog:wishlist"):
            r = self.client.get(reverse(name))
            self.assertEqual(r.status_code, 302)
            self.assertIn("/accounts/login/", r["Location"])

    def test_address_isolation(self):
        from .models import Address
        other = User.objects.create_user("eve", "eve@example.com", PW)
        addr = Address.objects.create(user=other, full_name="x", phone="09121234567", province="p",
                                      city="c", postal_code="1234567890", address="a")
        self.client.login(username="ali", password=PW)
        self.assertEqual(self.client.get(reverse("accounts:address_edit", args=[addr.pk])).status_code, 404)
        self.assertEqual(self.client.post(reverse("accounts:address_delete", args=[addr.pk])).status_code, 404)
