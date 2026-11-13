from django.contrib import admin, messages

from .models import Coupon, Order, OrderItem


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    can_delete = False
    readonly_fields = ("product", "product_name", "product_sku", "unit_price", "quantity")


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ("code", "user", "status", "total", "created_at")
    list_filter = ("status", "created_at")
    search_fields = ("code", "user__username", "phone", "full_name", "tracking_code")
    readonly_fields = ("code", "user", "subtotal", "discount", "shipping", "total", "coupon_code",
                       "paid_at", "created_at", "updated_at")
    inlines = [OrderItemInline]
    actions = ["mark_shipped", "mark_delivered"]

    @admin.action(description="علامت‌گذاری به‌عنوان «ارسال شده»")
    def mark_shipped(self, request, queryset):
        n = queryset.filter(status=Order.Status.PAID).update(status=Order.Status.SHIPPED)
        self.message_user(request, f"{n} سفارش ارسال‌شده ثبت شد.", messages.SUCCESS)

    @admin.action(description="علامت‌گذاری به‌عنوان «تحویل داده شده»")
    def mark_delivered(self, request, queryset):
        n = queryset.filter(status=Order.Status.SHIPPED).update(status=Order.Status.DELIVERED)
        self.message_user(request, f"{n} سفارش تحویل‌شده ثبت شد.", messages.SUCCESS)


@admin.register(Coupon)
class CouponAdmin(admin.ModelAdmin):
    list_display = ("code", "percent", "min_order", "used_count", "usage_limit", "valid_to", "is_active")
    list_editable = ("is_active",)
