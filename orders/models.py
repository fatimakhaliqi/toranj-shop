import secrets

from django.conf import settings
from django.db import models
from django.urls import reverse
from django.utils import timezone


class Coupon(models.Model):
    code = models.CharField("کد تخفیف", max_length=30, unique=True)
    percent = models.PositiveSmallIntegerField("درصد تخفیف")
    max_discount = models.PositiveBigIntegerField("سقف تخفیف (تومان)", null=True, blank=True)
    min_order = models.PositiveBigIntegerField("حداقل خرید (تومان)", default=0)
    valid_from = models.DateTimeField("شروع اعتبار", null=True, blank=True)
    valid_to = models.DateTimeField("پایان اعتبار", null=True, blank=True)
    usage_limit = models.PositiveIntegerField("حداکثر تعداد استفاده", null=True, blank=True)
    used_count = models.PositiveIntegerField("تعداد استفاده", default=0, editable=False)
    is_active = models.BooleanField("فعال", default=True)

    class Meta:
        verbose_name = "کد تخفیف"
        verbose_name_plural = "کدهای تخفیف"

    def __str__(self):
        return self.code

    def validate_for(self, subtotal):
        """اگر کد قابل استفاده نباشد پیام خطا برمی‌گرداند، وگرنه None."""
        now = timezone.now()
        if not self.is_active or not 1 <= self.percent <= 100:
            return "کد تخفیف معتبر نیست."
        if self.valid_from and now < self.valid_from:
            return "زمان استفاده از این کد هنوز شروع نشده است."
        if self.valid_to and now > self.valid_to:
            return "این کد تخفیف منقضی شده است."
        if self.usage_limit is not None and self.used_count >= self.usage_limit:
            return "ظرفیت استفاده از این کد تمام شده است."
        if subtotal < self.min_order:
            return f"حداقل مبلغ خرید برای این کد {self.min_order:,} تومان است."
        return None

    def discount_for(self, subtotal):
        amount = subtotal * self.percent // 100
        if self.max_discount:
            amount = min(amount, self.max_discount)
        return min(amount, subtotal)


def _new_code():
    return str(secrets.randbelow(9 * 10**9) + 10**9)


class Order(models.Model):
    class Status(models.TextChoices):
        PENDING = "pending", "در انتظار پرداخت"
        PAID = "paid", "پرداخت شده (در حال آماده‌سازی)"
        SHIPPED = "shipped", "ارسال شده"
        DELIVERED = "delivered", "تحویل داده شده"
        CANCELLED = "cancelled", "لغو شده"

    code = models.CharField("شماره سفارش", max_length=12, unique=True, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="orders",
                             verbose_name="مشتری")
    status = models.CharField("وضعیت", max_length=12, choices=Status.choices, default=Status.PENDING)

    full_name = models.CharField("نام گیرنده", max_length=150)
    phone = models.CharField("موبایل", max_length=11)
    province = models.CharField("استان", max_length=100)
    city = models.CharField("شهر", max_length=100)
    postal_code = models.CharField("کد پستی", max_length=10)
    address = models.TextField("آدرس", max_length=500)
    note = models.CharField("توضیحات مشتری", max_length=300, blank=True)

    subtotal = models.PositiveBigIntegerField("جمع کالاها", default=0)
    discount = models.PositiveBigIntegerField("تخفیف", default=0)
    shipping = models.PositiveBigIntegerField("هزینه ارسال", default=0)
    total = models.PositiveBigIntegerField("مبلغ قابل پرداخت", default=0)
    coupon_code = models.CharField("کد تخفیف", max_length=30, blank=True)

    tracking_code = models.CharField("کد رهگیری پست", max_length=50, blank=True)
    paid_at = models.DateTimeField("زمان پرداخت", null=True, blank=True)
    created_at = models.DateTimeField("تاریخ ثبت", auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "سفارش"
        verbose_name_plural = "سفارش‌ها"
        ordering = ["-created_at"]

    def __str__(self):
        return f"سفارش {self.code}"

    def save(self, *args, **kwargs):
        if not self.code:
            code = _new_code()
            while Order.objects.filter(code=code).exists():
                code = _new_code()
            self.code = code
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse("orders:detail", args=[self.code])

    @property
    def can_pay(self):
        return self.status == self.Status.PENDING

    @property
    def can_cancel(self):
        return self.status == self.Status.PENDING


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="items")
    product = models.ForeignKey("catalog.Product", null=True, blank=True, on_delete=models.SET_NULL,
                                related_name="order_items")
    product_name = models.CharField("نام محصول", max_length=200)
    product_sku = models.CharField("کد محصول", max_length=50)
    unit_price = models.PositiveBigIntegerField("قیمت واحد")
    quantity = models.PositiveIntegerField("تعداد")

    class Meta:
        verbose_name = "قلم سفارش"
        verbose_name_plural = "اقلام سفارش"

    @property
    def line_total(self):
        return self.unit_price * self.quantity
