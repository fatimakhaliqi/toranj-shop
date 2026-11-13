from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.http import require_POST

from catalog.models import Product
from config.ratelimit import ratelimit
from orders.models import Coupon

from .cart import Cart


def _back(request, default="cart:detail"):
    nxt = request.POST.get("next", "")
    if nxt and url_has_allowed_host_and_scheme(nxt, allowed_hosts={request.get_host()},
                                               require_https=request.is_secure()):
        return redirect(nxt)
    return redirect(default)


def _qty(request, default=1):
    try:
        return max(0, int(request.POST.get("quantity", default)))
    except (TypeError, ValueError):
        return default


def detail(request):
    cart = Cart(request)
    return render(request, "cart/detail.html", {"cart": cart, "items": cart.items()})


@require_POST
def add(request, pk):
    product = get_object_or_404(Product, pk=pk, is_active=True)
    cart = Cart(request)
    qty = max(1, _qty(request))
    current = cart.data.get(str(pk), 0)
    if product.stock < 1:
        messages.error(request, "این محصول موجود نیست.")
    elif current + qty > product.stock:
        messages.warning(request, "موجودی کافی نیست؛ تعداد به حداکثر موجودی تنظیم شد.")
        cart.set(product, product.stock)
    else:
        cart.add(product, qty)
        messages.success(request, "به سبد خرید اضافه شد.")
    return _back(request)


@require_POST
def update(request, pk):
    product = get_object_or_404(Product, pk=pk, is_active=True)
    cart = Cart(request)
    qty = _qty(request, 1)
    if qty > product.stock:
        messages.warning(request, "تعداد درخواستی بیشتر از موجودی است.")
    cart.set(product, qty)
    return redirect("cart:detail")


@require_POST
def remove(request, pk):
    Cart(request).remove(pk)
    messages.info(request, "از سبد خرید حذف شد.")
    return redirect("cart:detail")


@require_POST
@ratelimit("coupon", limit=15, window=3600)
def coupon_apply(request):
    code = request.POST.get("code", "").strip()[:30]
    cart = Cart(request)
    coupon = Coupon.objects.filter(code__iexact=code).first() if code else None
    error = coupon.validate_for(cart.subtotal) if coupon else "کد تخفیف معتبر نیست."
    if error:
        messages.error(request, error)
    else:
        request.session[Cart.COUPON_KEY] = coupon.code
        messages.success(request, "کد تخفیف اعمال شد.")
    return redirect("cart:detail")


@require_POST
def coupon_remove(request):
    request.session.pop(Cart.COUPON_KEY, None)
    return redirect("cart:detail")
