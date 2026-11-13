from django.contrib.sitemaps import Sitemap
from django.urls import reverse

from catalog.models import Category, Product


class StaticSitemap(Sitemap):
    priority, changefreq = 0.5, "monthly"

    def items(self):
        return ["home", "about", "faq", "terms", "contact", "catalog:list"]

    def location(self, item):
        return reverse(item)


class ProductSitemap(Sitemap):
    priority, changefreq = 0.8, "daily"

    def items(self):
        return Product.objects.filter(is_active=True, category__is_active=True)

    def lastmod(self, obj):
        return obj.updated_at


class CategorySitemap(Sitemap):
    priority, changefreq = 0.7, "weekly"

    def items(self):
        return Category.objects.filter(is_active=True)


SITEMAPS = {"static": StaticSitemap, "products": ProductSitemap, "categories": CategorySitemap}
