from django.contrib.auth import views as auth_views
from django.urls import path, reverse_lazy
from django.views.generic import TemplateView

from . import views

app_name = "accounts"

urlpatterns = [
    path("login/", views.ThrottledLoginView.as_view(), name="login"),
    path("logout/", auth_views.LogoutView.as_view(), name="logout"),
    path("register/", views.register, name="register"),
    path("dashboard/", views.dashboard, name="dashboard"),
    path("addresses/", views.address_list, name="addresses"),
    path("addresses/new/", views.address_edit, name="address_new"),
    path("addresses/<int:pk>/edit/", views.address_edit, name="address_edit"),
    path("addresses/<int:pk>/delete/", views.address_delete, name="address_delete"),
    path("password/change/", views.PasswordChange.as_view(), name="password_change"),
    path("password/reset/", views.reset_view, name="password_reset"),
    path("password/reset/sent/", TemplateView.as_view(
        template_name="accounts/message.html",
        extra_context={"title": "ایمیل ارسال شد",
                       "text": "اگر ایمیل شما در سیستم باشد، لینک بازیابی رمز برایتان ارسال می‌شود."}),
        name="password_reset_done"),
    path("password/reset/<uidb64>/<token>/", auth_views.PasswordResetConfirmView.as_view(
        template_name="accounts/form.html",
        success_url=reverse_lazy("accounts:password_reset_complete"),
        extra_context={"title": "رمز جدید", "button": "ثبت رمز جدید"}),
        name="password_reset_confirm"),
    path("password/reset/complete/", TemplateView.as_view(
        template_name="accounts/message.html",
        extra_context={"title": "رمز عبور تغییر کرد", "text": "اکنون می‌توانید وارد شوید.",
                       "link": "accounts:login", "link_text": "ورود"}),
        name="password_reset_complete"),
]
