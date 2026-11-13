from django.test import TestCase
from django.urls import reverse

from .models import Category, Product


def make_product(**kw):
    cat = kw.pop("category", None) or Category.objects.create(name="دسته")
    defaults = dict(category=cat, name="کالا", sku="S1", price=1000, stock=5)
    defaults.update(kw)
    return Product.objects.create(**defaults)


class CatalogTests(TestCase):
    def test_slug_generated_and_unique(self):
        a, b = make_product(sku="A"), make_product(sku="B")
        self.assertNotEqual(a.slug, b.slug)

    def test_list_search_filters(self):
        make_product(name="گوشی", sku="A", price=500)
        make_product(name="لپ‌تاپ", sku="B", price=5000)
        r = self.client.get(reverse("catalog:list"), {"q": "گوشی"})
        self.assertContains(r, "گوشی")
        self.assertNotContains(r, "لپ‌تاپ")
        r = self.client.get(reverse("catalog:list"), {"min": "1000", "sort": "cheap"})
        self.assertNotContains(r, "گوشی")

    def test_bad_params_do_not_crash(self):
        make_product()
        r = self.client.get(reverse("catalog:list"), {"min": "abc", "max": "-5", "page": "zzz", "sort": "evil"})
        self.assertEqual(r.status_code, 200)

    def test_detail_and_inactive_hidden(self):
        p = make_product()
        self.assertEqual(self.client.get(p.get_absolute_url()).status_code, 200)
        p.is_active = False
        p.save()
        self.assertEqual(self.client.get(p.get_absolute_url()).status_code, 404)

    def test_home_renders(self):
        make_product(is_featured=True)
        self.assertEqual(self.client.get(reverse("home")).status_code, 200)
