from django.contrib import messages
from django.db.models import F
from django.http import HttpResponse
from django.shortcuts import redirect, render
from django.views.decorators.http import require_GET

from catalog.models import Category, Product
from catalog.views import with_rating
from config.ratelimit import ratelimit

from .forms import ContactForm


def _products():
    return Product.objects.filter(is_active=True, category__is_active=True).prefetch_related("images")


def home(request):
    return render(request, "pages/home.html", {
        "categories": Category.objects.filter(is_active=True, parent__isnull=True)[:10],
        "deals": with_rating(_products().filter(compare_at_price__gt=F("price"), stock__gt=0))
                 .order_by("-created_at")[:8],
        "newest": with_rating(_products()).order_by("-created_at")[:8],
        "bestsellers": with_rating(_products().filter(sold_count__gt=0)).order_by("-sold_count")[:8],
        "featured": with_rating(_products().filter(is_featured=True))[:4],
    })


@ratelimit("contact", limit=5, window=3600)
def contact(request):
    form = ContactForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        form.instance.save()
        messages.success(request, "پیام شما ارسال شد. به‌زودی پاسخ می‌دهیم.")
        return redirect("contact")
    return render(request, "pages/contact.html", {"form": form})


@require_GET
def robots(request):
    from django.conf import settings
    from django.urls import reverse
    lines = ["User-agent: *", "Disallow: /" + settings.ADMIN_URL, "Disallow: /cart/", "Disallow: /orders/",
             "Disallow: /accounts/", "Disallow: /payments/",
             "Sitemap: " + request.build_absolute_uri(reverse("sitemap"))]
    return HttpResponse("\n".join(lines), content_type="text/plain")


def error_404(request, exception=None):
    return render(request, "404.html", status=404)


def error_500(request):
    return render(request, "500.html", status=500)
