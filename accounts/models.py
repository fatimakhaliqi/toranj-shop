from django.contrib.auth.models import AbstractUser
from django.core.validators import RegexValidator
from django.db import models

phone_validator = RegexValidator(r"^09\d{9}$", "شماره موبایل باید مثل 09121234567 باشد.")
postal_validator = RegexValidator(r"^\d{10}$", "کد پستی باید ۱۰ رقم باشد.")


class User(AbstractUser):
    email = models.EmailField("ایمیل", unique=True)
    phone = models.CharField("موبایل", max_length=11, blank=True, validators=[phone_validator])

    class Meta:
        verbose_name = "کاربر"
        verbose_name_plural = "کاربران"


class Address(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="addresses", verbose_name="کاربر")
    full_name = models.CharField("نام گیرنده", max_length=150)
    phone = models.CharField("موبایل گیرنده", max_length=11, validators=[phone_validator])
    province = models.CharField("استان", max_length=100)
    city = models.CharField("شهر", max_length=100)
    postal_code = models.CharField("کد پستی", max_length=10, validators=[postal_validator])
    address = models.TextField("آدرس کامل", max_length=500)
    is_default = models.BooleanField("آدرس پیش‌فرض", default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "آدرس"
        verbose_name_plural = "آدرس‌ها"
        ordering = ["-is_default", "-created_at"]

    def __str__(self):
        return f"{self.full_name} - {self.city}"

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        if self.is_default:
            Address.objects.filter(user=self.user).exclude(pk=self.pk).update(is_default=False)
