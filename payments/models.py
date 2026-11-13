from django.db import models


class Payment(models.Model):
    class Status(models.TextChoices):
        PENDING = "pending", "در انتظار پرداخت"
        SUCCESS = "success", "موفق"
        FAILED = "failed", "ناموفق"

    order = models.ForeignKey("orders.Order", on_delete=models.PROTECT, related_name="payments",
                              verbose_name="سفارش")
    gateway = models.CharField("درگاه", max_length=30)
    amount = models.PositiveBigIntegerField("مبلغ (تومان)")
    authority = models.CharField("شناسه درگاه", max_length=100, unique=True)
    ref_id = models.CharField("شماره پیگیری", max_length=100, blank=True)
    status = models.CharField("وضعیت", max_length=10, choices=Status.choices, default=Status.PENDING)
    message = models.CharField("پیام", max_length=200, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    paid_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = "پرداخت"
        verbose_name_plural = "پرداخت‌ها"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.order.code} / {self.status}"
