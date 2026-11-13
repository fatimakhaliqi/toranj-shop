from django.conf import settings

from cart.cart import Cart
from catalog.models import Category


def site(request):
    return {
        "SITE_NAME": settings.SITE_NAME,
        "SITE_TAGLINE": settings.SITE_TAGLINE,
        "SUPPORT_PHONE": settings.SUPPORT_PHONE,
        "SUPPORT_EMAIL": settings.SUPPORT_EMAIL,
        "FREE_SHIPPING_THRESHOLD": settings.FREE_SHIPPING_THRESHOLD,
        "nav_categories": Category.objects.filter(is_active=True, parent__isnull=True)[:8],
        "cart_count": len(Cart(request)) if hasattr(request, "session") else 0,
    }
