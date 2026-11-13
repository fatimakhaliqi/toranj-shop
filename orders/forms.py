from django import forms

from accounts.models import Address
from accounts.utils import clean_phone, to_en_digits


class CheckoutForm(forms.Form):
    saved_address = forms.ModelChoiceField(queryset=Address.objects.none(), required=False,
                                           empty_label="— آدرس جدید —", label="آدرس‌های ذخیره‌شده")
    full_name = forms.CharField(label="نام گیرنده", max_length=150, required=False)
    phone = forms.CharField(label="موبایل", max_length=15, required=False)
    province = forms.CharField(label="استان", max_length=100, required=False)
    city = forms.CharField(label="شهر", max_length=100, required=False)
    postal_code = forms.CharField(label="کد پستی", max_length=15, required=False)
    address = forms.CharField(label="آدرس کامل", max_length=500, required=False,
                              widget=forms.Textarea(attrs={"rows": 3}))
    save_address = forms.BooleanField(label="ذخیره این آدرس برای دفعات بعد", required=False)
    note = forms.CharField(label="توضیحات (اختیاری)", max_length=300, required=False)

    def __init__(self, *args, user, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["saved_address"].queryset = Address.objects.filter(user=user)

    def clean(self):
        data = super().clean()
        saved = data.get("saved_address")
        if saved:
            data.update(full_name=saved.full_name, phone=saved.phone, province=saved.province,
                        city=saved.city, postal_code=saved.postal_code, address=saved.address)
            return data
        for name in ("full_name", "phone", "province", "city", "postal_code", "address"):
            if not (data.get(name) or "").strip():
                self.add_error(name, "این فیلد الزامی است.")
        if not self.errors:
            phone = clean_phone(data["phone"])
            if not phone:
                self.add_error("phone", "شماره موبایل معتبر نیست (مثال: 09121234567).")
            code = to_en_digits(data["postal_code"])
            if not (code.isdigit() and len(code) == 10):
                self.add_error("postal_code", "کد پستی باید ۱۰ رقم باشد.")
            if not self.errors:
                data["phone"], data["postal_code"] = phone, code
        return data
