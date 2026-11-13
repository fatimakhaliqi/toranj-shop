from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm

from .models import Address
from .utils import clean_phone, to_en_digits

User = get_user_model()


class RegisterForm(UserCreationForm):
    email = forms.EmailField(label="ایمیل")
    phone = forms.CharField(label="موبایل (اختیاری)", required=False, max_length=15)

    class Meta:
        model = User
        fields = ("username", "email", "phone", "password1", "password2")

    def clean_email(self):
        email = self.cleaned_data["email"].strip().lower()
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError("این ایمیل قبلا ثبت شده است.")
        return email

    def clean_phone(self):
        raw = self.cleaned_data.get("phone", "")
        if not raw:
            return ""
        phone = clean_phone(raw)
        if not phone:
            raise forms.ValidationError("شماره موبایل معتبر نیست.")
        return phone


class LoginForm(AuthenticationForm):
    username = forms.CharField(label="نام کاربری یا ایمیل", max_length=254)
    error_messages = {
        "invalid_login": "نام کاربری/ایمیل یا رمز عبور نادرست است.",
        "inactive": "این حساب غیرفعال است.",
    }


class ProfileForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ("first_name", "last_name", "phone")
        labels = {"first_name": "نام", "last_name": "نام خانوادگی", "phone": "موبایل"}

    def clean_phone(self):
        raw = self.cleaned_data.get("phone", "")
        if not raw:
            return ""
        phone = clean_phone(raw)
        if not phone:
            raise forms.ValidationError("شماره موبایل معتبر نیست.")
        return phone


class AddressForm(forms.ModelForm):
    class Meta:
        model = Address
        fields = ("full_name", "phone", "province", "city", "postal_code", "address", "is_default")
        widgets = {"address": forms.Textarea(attrs={"rows": 3})}

    def clean_phone(self):
        phone = clean_phone(self.cleaned_data["phone"])
        if not phone:
            raise forms.ValidationError("شماره موبایل معتبر نیست (مثال: 09121234567).")
        return phone

    def clean_postal_code(self):
        code = to_en_digits(self.cleaned_data["postal_code"])
        if not (code.isdigit() and len(code) == 10):
            raise forms.ValidationError("کد پستی باید ۱۰ رقم باشد.")
        return code
