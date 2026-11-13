import logging

from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth import views as auth_views
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy
from django.views.decorators.http import require_POST

from config.ratelimit import client_ip, hit, ratelimit

from . import throttle
from .forms import AddressForm, LoginForm, ProfileForm, RegisterForm
from .models import Address

logger = logging.getLogger("accounts")


class ThrottledLoginView(auth_views.LoginView):
    """ورود با قفل موقت بعد از چند تلاش ناموفق (ضد brute-force)."""

    template_name = "accounts/form.html"
    authentication_form = LoginForm
    redirect_authenticated_user = True
    extra_context = {"title": "ورود به حساب", "button": "ورود", "is_login": True}

    def post(self, request, *args, **kwargs):
        username = request.POST.get("username", "")
        if throttle.is_locked(request, username):
            logger.warning("login locked: user=%s ip=%s", username, client_ip(request))
            messages.error(request, "تلاش‌های ناموفق زیاد بود. ۱۵ دقیقه بعد دوباره امتحان کنید.")
            return self.get(request, *args, **kwargs)
        return super().post(request, *args, **kwargs)

    def form_invalid(self, form):
        throttle.register_failure(self.request, self.request.POST.get("username", ""))
        return super().form_invalid(form)

    def form_valid(self, form):
        throttle.reset(self.request, self.request.POST.get("username", ""))
        return super().form_valid(form)


@ratelimit("register", limit=10, window=3600)
def register(request):
    if request.user.is_authenticated:
        return redirect("home")
    form = RegisterForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        user = form.save(commit=False)
        user.email = form.cleaned_data["email"]
        user.phone = form.cleaned_data["phone"]
        user.save()
        login(request, user, backend="accounts.backends.EmailOrUsernameBackend")
        messages.success(request, "ثبت‌نام با موفقیت انجام شد. خوش آمدید!")
        return redirect("home")
    return render(request, "accounts/form.html",
                  {"form": form, "title": "ثبت‌نام", "button": "ایجاد حساب"})


@login_required
def dashboard(request):
    form = ProfileForm(request.POST or None, instance=request.user)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "اطلاعات شما ذخیره شد.")
        return redirect("accounts:dashboard")
    orders = request.user.orders.all()[:3]
    return render(request, "accounts/dashboard.html", {"form": form, "orders": orders})


@login_required
def address_list(request):
    return render(request, "accounts/addresses.html", {"addresses": request.user.addresses.all()})


@login_required
def address_edit(request, pk=None):
    instance = get_object_or_404(Address, pk=pk, user=request.user) if pk else None
    form = AddressForm(request.POST or None, instance=instance)
    if request.method == "POST" and form.is_valid():
        address = form.save(commit=False)
        address.user = request.user
        address.save()
        messages.success(request, "آدرس ذخیره شد.")
        return redirect(request.GET.get("next") if request.GET.get("next", "").startswith("/")
                        and not request.GET.get("next", "").startswith("//") else "accounts:addresses")
    return render(request, "accounts/form.html",
                  {"form": form, "title": "ویرایش آدرس" if pk else "افزودن آدرس", "button": "ذخیره"})


@login_required
@require_POST
def address_delete(request, pk):
    get_object_or_404(Address, pk=pk, user=request.user).delete()
    messages.success(request, "آدرس حذف شد.")
    return redirect("accounts:addresses")


# --- تغییر و بازیابی رمز عبور ---
class PasswordChange(auth_views.PasswordChangeView):
    template_name = "accounts/form.html"
    success_url = reverse_lazy("accounts:dashboard")
    extra_context = {"title": "تغییر رمز عبور", "button": "تغییر رمز"}

    def form_valid(self, form):
        messages.success(self.request, "رمز عبور تغییر کرد.")
        return super().form_valid(form)


reset_view = ratelimit("pwreset", limit=5, window=3600)(
    auth_views.PasswordResetView.as_view(
        template_name="accounts/form.html",
        email_template_name="accounts/password_reset_email.txt",
        subject_template_name="accounts/password_reset_subject.txt",
        success_url=reverse_lazy("accounts:password_reset_done"),
        extra_context={"title": "بازیابی رمز عبور", "button": "ارسال لینک بازیابی",
                       "hint": "ایمیل حساب خود را وارد کنید."},
    )
)
