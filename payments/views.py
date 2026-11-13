import logging

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_GET, require_POST

from config.ratelimit import ratelimit
from orders.models import Order

from .gateways import GatewayError
from .models import Payment
from .services import start_payment, verify_payment

logger = logging.getLogger("payments")


@login_required
@require_POST
@ratelimit("payment-start", limit=20, window=3600)
def start(request, code):
    order = get_object_or_404(Order, code=code, user=request.user)
    if not order.can_pay:
        messages.error(request, "این سفارش قابل پرداخت نیست.")
        return redirect(order)
    try:
        return redirect(start_payment(request, order))
    except GatewayError as exc:
        logger.error("start payment failed order=%s: %s", order.code, exc)
        messages.error(request, "اتصال به درگاه پرداخت ممکن نشد. کمی بعد دوباره تلاش کنید.")
        return redirect(order)


@require_GET
def callback(request):
    authority = request.GET.get("Authority", "")[:100]
    payment = verify_payment(authority, request.GET.get("Status", ""))
    if payment is None:
        raise Http404
    if payment.status == Payment.Status.SUCCESS:
        messages.success(request, f"پرداخت موفق بود. شماره پیگیری: {payment.ref_id}")
    elif payment.status == Payment.Status.FAILED:
        messages.error(request, "پرداخت انجام نشد. در صورت کسر وجه، مبلغ تا ۷۲ ساعت برمی‌گردد.")
    else:
        messages.warning(request, "نتیجه‌ی پرداخت هنوز مشخص نیست؛ کمی بعد وضعیت سفارش را بررسی کنید.")
    return redirect(payment.order)


def mock(request, authority):
    """صفحه‌ی درگاه آزمایشی (فقط DEBUG)."""
    if not settings.DEBUG:
        raise Http404
    payment = get_object_or_404(Payment, authority=authority, gateway="mock")
    return render(request, "payments/mock.html", {"payment": payment})
