from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.urls import reverse
from django.utils.text import slugify


def _unique_slug(model, base, instance_pk):
    base = slugify(base, allow_unicode=True) or "item"
    slug, n = base, 1
    while model.objects.filter(slug=slug).exclude(pk=instance_pk).exists():
        n += 1
        slug = f"{base}-{n}"
    return slug


class Category(models.Model):
    name = models.CharField("نام", max_length=120)
    slug = models.SlugField("نامک (آدرس)", max_length=140, unique=True, allow_unicode=True, blank=True)
    icon = models.CharField("آیکون (ایموجی)", max_length=8, blank=True, default="🛍️")
    parent = models.ForeignKey("self", null=True, blank=True, on_delete=models.SET_NULL,
                               related_name="children", verbose_name="دسته والد")
    image = models.ImageField("تصویر", upload_to="categories/", blank=True)
    is_active = models.BooleanField("فعال", default=True)
    sort_order = models.PositiveIntegerField("ترتیب", default=0)

    class Meta:
        verbose_name = "دسته‌بندی"
        verbose_name_plural = "دسته‌بندی‌ها"
        ordering = ["sort_order", "name"]

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = _unique_slug(Category, self.name, self.pk)
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse("catalog:category", args=[self.slug])

    def family_ids(self):
        return [self.pk] + list(self.children.values_list("pk", flat=True))


class Product(models.Model):
    category = models.ForeignKey(Category, on_delete=models.PROTECT, related_name="products",
                                 verbose_name="دسته‌بندی")
    name = models.CharField("نام محصول", max_length=200)
    slug = models.SlugField("نامک (آدرس)", max_length=220, unique=True, allow_unicode=True, blank=True)
    sku = models.CharField("کد محصول", max_length=50, unique=True)
    short_description = models.CharField("توضیح کوتاه", max_length=300, blank=True)
    description = models.TextField("توضیحات کامل", blank=True)
    price = models.PositiveBigIntegerField("قیمت (تومان)")
    compare_at_price = models.PositiveBigIntegerField("قیمت قبل از تخفیف (تومان)", null=True, blank=True)
    stock = models.PositiveIntegerField("موجودی", default=0)
    sold_count = models.PositiveIntegerField("تعداد فروش", default=0, editable=False)
    is_active = models.BooleanField("فعال", default=True)
    is_featured = models.BooleanField("ویژه (نمایش در صفحه اول)", default=False)
    created_at = models.DateTimeField("تاریخ ایجاد", auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "محصول"
        verbose_name_plural = "محصولات"
        ordering = ["-created_at"]
        indexes = [models.Index(fields=["is_active", "-created_at"])]

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = _unique_slug(Product, self.name, self.pk)
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse("catalog:detail", args=[self.pk, self.slug])

    @property
    def discount_percent(self):
        if self.compare_at_price and self.compare_at_price > self.price:
            return round((self.compare_at_price - self.price) * 100 / self.compare_at_price)
        return 0

    @property
    def in_stock(self):
        return self.stock > 0

    @property
    def main_image(self):
        first = self.images.all()[:1]
        return first[0].image if first else None


class ProductImage(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="images", verbose_name="محصول")
    image = models.ImageField("تصویر", upload_to="products/%Y/%m/")
    alt = models.CharField("متن جایگزین", max_length=200, blank=True)
    sort_order = models.PositiveIntegerField("ترتیب", default=0)

    class Meta:
        verbose_name = "تصویر محصول"
        verbose_name_plural = "تصاویر محصول"
        ordering = ["sort_order", "id"]


class Review(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="reviews")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="reviews")
    rating = models.PositiveSmallIntegerField("امتیاز", validators=[MinValueValidator(1), MaxValueValidator(5)])
    comment = models.TextField("نظر", max_length=1000)
    is_approved = models.BooleanField("تأیید شده", default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "نظر"
        verbose_name_plural = "نظرات"
        ordering = ["-created_at"]
        constraints = [models.UniqueConstraint(fields=["product", "user"], name="one_review_per_user")]

    def __str__(self):
        return f"{self.user} → {self.product} ({self.rating})"


class WishlistItem(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="wishlist")
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="wished_by")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "علاقه‌مندی"
        verbose_name_plural = "علاقه‌مندی‌ها"
        ordering = ["-created_at"]
        constraints = [models.UniqueConstraint(fields=["user", "product"], name="unique_wishlist_item")]
