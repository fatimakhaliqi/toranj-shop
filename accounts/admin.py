from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import Address, User


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = ("username", "email", "phone", "is_staff", "is_active", "date_joined")
    fieldsets = UserAdmin.fieldsets + (("اطلاعات تماس", {"fields": ("phone",)}),)
    add_fieldsets = UserAdmin.add_fieldsets + ((None, {"fields": ("email", "phone")}),)
    search_fields = ("username", "email", "phone")


@admin.register(Address)
class AddressAdmin(admin.ModelAdmin):
    list_display = ("user", "full_name", "city", "phone", "is_default")
    search_fields = ("user__username", "full_name", "phone", "postal_code")
