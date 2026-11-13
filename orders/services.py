from datetime import timedelta

from django.conf import settings
from django.db import transaction
from django.db.models import F
from django.utils import timezone

from catalog.models import Product

from .models import Coupon, Order, OrderItem
from .pricing import shipping_cost


class OrderError(Exception):
    pass


@transaction.atomic
def create_order(user, cart, data):
    """ساخت سفارش از روی سبد؛ قیمت و موجودی همیشه از دیتابیس خوانده می‌شود."""
    lines = cart.items()
    if not lines:
        raise OrderError("سبد خرید شما خالی است.")

    ids = sorted(line["product"].pk for line in lines)
    locked = {p.pk: p for p in Product.objects.select_for_update()
              .filter(pk__in=ids, is_active=True).order_by("pk")}

    subtotal, rows = 0, []
    for line in lines:
        product, qty = locked.get(line["product"].pk), line["quantity"]
        if product is None or qty < 1 or product.stock < qty:
            raise OrderError(f"موجودی «{line['product'].name}» کافی نیست.")
        subtotal += product.price * qty
        rows.append((product, qty))

    coupon, discount = None, 0
    if cart.coupon_code:
        coupon = Coupon.objects.select_for_update().filter(code__iexact=cart.coupon_code).first()
        error = coupon.validate_for(subtotal) if coupon else "کد تخفیف معتبر نیست."
        if error:
            raise OrderError(error)
        discount = coupon.discount_for(subtotal)

    shipping = shipping_cost(subtotal - discount)
    order = Order.objects.create(
        user=user,
        full_name=data["full_name"], phone=data["phone"], province=data["province"], city=data["city"],
        postal_code=data["postal_code"], address=data["address"], note=data.get("note", ""),
        subtotal=subtotal, discount=discount, shipping=shipping,
        total=subtotal - discount + shipping,
        coupon_code=coupon.code if coupon else "",
    )
    OrderItem.objects.bulk_create([
        OrderItem(order=order, product=p, product_name=p.name, product_sku=p.sku,
                  unit_price=p.price, quantity=q) for p, q in rows
    ])
    for product, qty in rows:
        Product.objects.filter(pk=product.pk).update(stock=F("stock") - qty)
    if coupon:
        Coupon.objects.filter(pk=coupon.pk).update(used_count=F("used_count") + 1)
    cart.clear()
    return order


@transaction.atomic
def cancel_order(order):
    """لغو سفارش پرداخت‌نشده و بازگرداندن موجودی."""
    order = Order.objects.select_for_update().get(pk=order.pk)
    if order.status != Order.Status.PENDING:
        raise OrderError("فقط سفارش پرداخت‌نشده قابل لغو است.")
    for item in order.items.all():
        if item.product_id:
            Product.objects.filter(pk=item.product_id).update(stock=F("stock") + item.quantity)
    if order.coupon_code:
        Coupon.objects.filter(code=order.coupon_code, used_count__gt=0).update(used_count=F("used_count") - 1)
    order.status = Order.Status.CANCELLED
    order.save(update_fields=["status", "updated_at"])
    return order


def expire_unpaid_orders():
    limit = timezone.now() - timedelta(minutes=settings.ORDER_PAYMENT_TIMEOUT_MINUTES)
    count = 0
    for order in Order.objects.filter(status=Order.Status.PENDING, created_at__lt=limit):
        try:
            cancel_order(order)
            count += 1
        except OrderError:
            pass
    return count
