from django import forms

from .models import ContactMessage


class ContactForm(forms.ModelForm):
    website = forms.CharField(required=False, widget=forms.TextInput(attrs={"tabindex": "-1", "autocomplete": "off"}))

    class Meta:
        model = ContactMessage
        fields = ("name", "email", "subject", "message")
        widgets = {"message": forms.Textarea(attrs={"rows": 5})}

    def clean_website(self):  # honeypot ضد ربات
        if self.cleaned_data.get("website"):
            raise forms.ValidationError("درخواست نامعتبر.")
        return ""
