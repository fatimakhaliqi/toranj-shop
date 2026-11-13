import logging

from django.db import transaction
from django.db.models import F
from django.urls import reverse
from django.utils import timezone

from catalog.models import Product
from orders.models import Order

from .gateways import GatewayError, get_gateway
from .models import Payment

logger = logging.getLogger("payments")


def start_payment(request, order):
    """ایجاد تراکنش و برگرداندن آدرس درگاه."""
    gateway = get_gateway()
    payment = Payment(order=order, gateway=gateway.name, amount=order.total)
    callback = request.build_absolute_uri(reverse("payments:callback"))
    payment.authority = gateway.request(payment, callback, mobile=order.phone)
    payment.save()
    return gateway.start_url(payment)


def verify_payment(authority, status_param):
    """
    تأیید پرداخت (idempotent). خروجی: (payment یا None)
    مبلغ همیشه از دیتابیس خوانده می‌شود، نه از ورودی کاربر.
    """
    gateway_error = None
    with transaction.atomic():
        payment = (Payment.objects.select_for_update().select_related("order")
                   .filter(authority=authority).first())
        if payment is None:
            return None
        if payment.status != Payment.Status.PENDING:
            return payment
        order = Order.objects.select_for_update().get(pk=payment.order_id)

        if order.status != Order.Status.PENDING:
            # سفارش لغو شده؛ تأیید نمی‌کنیم تا مبلغ خودکار به حساب مشتری برگردد.
            payment.status, payment.message = Payment.Status.FAILED, "سفارش دیگر فعال نیست"
            payment.save(update_fields=["status", "message"])
            return payment

        try:
            ok, ref_id = get_gateway().verify(payment, status_param)
        except GatewayError as exc:
            gateway_error = exc
            ok, ref_id = False, ""

        if gateway_error:
            # وضعیت را pending نگه می‌داریم تا کاربر بتواند دوباره تأیید را امتحان کند
            logger.error("gateway error on verify: %s", gateway_error)
            return payment
        if ok:
            now = timezone.now()
            payment.status, payment.ref_id, payment.paid_at = Payment.Status.SUCCESS, ref_id, now
            payment.save(update_fields=["status", "ref_id", "paid_at"])
            order.status, order.paid_at = Order.Status.PAID, now
            order.save(update_fields=["status", "paid_at", "updated_at"])
            for item in order.items.all():
                if item.product_id:
                    Product.objects.filter(pk=item.product_id).update(sold_count=F("sold_count") + item.quantity)
            logger.info("payment success order=%s ref=%s", order.code, ref_id)
        else:
            payment.status, payment.message = Payment.Status.FAILED, "پرداخت ناموفق یا لغو شد"
            payment.save(update_fields=["status", "message"])
    return payment
