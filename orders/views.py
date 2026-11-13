from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from accounts.models import Address
from cart.cart import Cart

from .forms import CheckoutForm
from .models import Order
from .services import OrderError, cancel_order, create_order


@login_required
def checkout(request):
    cart = Cart(request)
    if not cart.items():
        messages.error(request, "سبد خرید شما خالی است.")
        return redirect("cart:detail")
    form = CheckoutForm(request.POST or None, user=request.user)
    if request.method == "POST" and form.is_valid():
        data = form.cleaned_data
        try:
            order = create_order(request.user, cart, data)
        except OrderError as exc:
            messages.error(request, str(exc))
            return redirect("cart:detail")
        if data.get("save_address") and not data.get("saved_address"):
            Address.objects.create(
                user=request.user, full_name=data["full_name"], phone=data["phone"],
                province=data["province"], city=data["city"], postal_code=data["postal_code"],
                address=data["address"], is_default=not request.user.addresses.exists())
        messages.success(request, "سفارش ثبت شد. برای نهایی‌شدن، پرداخت را انجام دهید.")
        return redirect(order)
    return render(request, "orders/checkout.html", {"form": form, "cart": cart})


@login_required
def order_list(request):
    return render(request, "orders/list.html", {"orders": request.user.orders.all()})


@login_required
def order_detail(request, code):
    order = get_object_or_404(Order.objects.prefetch_related("items"), code=code, user=request.user)
    return render(request, "orders/detail.html", {"order": order})


@login_required
@require_POST
def order_cancel(request, code):
    order = get_object_or_404(Order, code=code, user=request.user)
    try:
        cancel_order(order)
        messages.success(request, "سفارش لغو شد.")
    except OrderError as exc:
        messages.error(request, str(exc))
    return redirect(order)
