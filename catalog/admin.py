from django.contrib import admin, messages

from .models import Category, Product, ProductImage, Review, WishlistItem


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "icon", "parent", "is_active", "sort_order")
    list_editable = ("is_active", "sort_order")
    search_fields = ("name",)


class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 1


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ("name", "sku", "category", "price", "compare_at_price", "stock", "is_active", "is_featured")
    list_editable = ("price", "stock", "is_active", "is_featured")
    list_filter = ("is_active", "is_featured", "category")
    search_fields = ("name", "sku")
    inlines = [ProductImageInline]
    list_per_page = 50


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ("product", "user", "rating", "is_approved", "created_at")
    list_filter = ("is_approved", "rating")
    actions = ["approve"]

    @admin.action(description="تأیید نظرهای انتخاب‌شده")
    def approve(self, request, queryset):
        n = queryset.update(is_approved=True)
        self.message_user(request, f"{n} نظر تأیید شد.", messages.SUCCESS)


admin.site.register(WishlistItem)
