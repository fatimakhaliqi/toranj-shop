from django import forms

from .models import Review


class ReviewForm(forms.ModelForm):
    rating = forms.TypedChoiceField(label="امتیاز", coerce=int,
                                    choices=[(i, f"{i} ستاره") for i in range(5, 0, -1)])

    class Meta:
        model = Review
        fields = ("rating", "comment")
        labels = {"comment": "نظر شما"}
        widgets = {"comment": forms.Textarea(attrs={"rows": 4})}
