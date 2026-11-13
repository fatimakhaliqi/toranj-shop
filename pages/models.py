from django.db import models


class ContactMessage(models.Model):
    name = models.CharField("نام", max_length=100)
    email = models.EmailField("ایمیل")
    subject = models.CharField("موضوع", max_length=150)
    message = models.TextField("پیام", max_length=2000)
    is_read = models.BooleanField("خوانده شده", default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "پیام تماس"
        verbose_name_plural = "پیام‌های تماس"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.name}: {self.subject}"
