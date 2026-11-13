from django.test import TestCase
from django.urls import reverse


class PagesTests(TestCase):
    def test_static_pages(self):
        for name in ("home", "about", "faq", "terms", "contact", "robots", "catalog:list"):
            self.assertEqual(self.client.get(reverse(name)).status_code, 200, name)

    def test_sitemap(self):
        self.assertEqual(self.client.get(reverse("sitemap")).status_code, 200)

    def test_contact_honeypot_and_save(self):
        from .models import ContactMessage
        data = {"name": "a", "email": "a@b.com", "subject": "s", "message": "m"}
        self.client.post(reverse("contact"), {**data, "website": "spam"})
        self.assertEqual(ContactMessage.objects.count(), 0)
        self.client.post(reverse("contact"), data)
        self.assertEqual(ContactMessage.objects.count(), 1)

    def test_security_headers(self):
        r = self.client.get(reverse("home"))
        self.assertIn("default-src 'self'", r["Content-Security-Policy"])
        self.assertEqual(r["X-Frame-Options"], "DENY")
