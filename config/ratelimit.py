"""محدودکننده‌ی ساده‌ی نرخ درخواست بر پایه‌ی کش جنگو."""
from functools import wraps

from django.conf import settings
from django.contrib import messages
from django.core.cache import cache
from django.shortcuts import redirect


def client_ip(request):
    if settings.BEHIND_PROXY:
        xff = request.META.get("HTTP_X_FORWARDED_FOR", "")
        if xff:
            return xff.split(",")[-1].strip()
    return request.META.get("REMOTE_ADDR", "unknown")


def hit(request, scope, limit, window, extra=""):
    """یک درخواست ثبت می‌کند؛ اگر از حد گذشته باشد False برمی‌گرداند."""
    key = f"rl:{scope}:{client_ip(request)}:{extra}"
    cache.add(key, 0, window)
    try:
        count = cache.incr(key)
    except ValueError:
        cache.set(key, 1, window)
        count = 1
    return count <= limit


def ratelimit(scope, limit=10, window=3600):
    """دکوراتور: فقط روی POST اعمال می‌شود."""
    def deco(view):
        @wraps(view)
        def wrapper(request, *args, **kwargs):
            if request.method == "POST" and not hit(request, scope, limit, window):
                messages.error(request, "تعداد درخواست‌های شما زیاد بود؛ کمی بعد دوباره تلاش کنید.")
                return redirect(request.META.get("HTTP_REFERER") or "home")
            return view(request, *args, **kwargs)
        return wrapper
    return deco
