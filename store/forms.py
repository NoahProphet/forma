from datetime import date

from django import forms
from django.utils import timezone

from .models import Inquiry

NORMALIZE_DIGITS = str.maketrans("۰۱۲۳۴۵۶۷۸۹٠١٢٣٤٥٦٧٨٩", "01234567890123456789")


def normalize_number(value):
    return value.translate(NORMALIZE_DIGITS)


class QuantityForm(forms.Form):
    quantity = forms.IntegerField(min_value=1, max_value=99, localize=False)

    def __init__(self, data):
        data = data.copy()
        data["quantity"] = normalize_number(data.get("quantity", ""))
        super().__init__(data)


class InquiryForm(forms.ModelForm):
    preferred_date = forms.DateField(
        label="روز پیشنهادی به میلادی",
        required=False,
        input_formats=["%Y-%m-%d"],
        widget=forms.DateInput(format="%Y-%m-%d", attrs={"type": "date", "dir": "ltr"}),
    )

    class Meta:
        model = Inquiry
        fields = ("name", "phone", "preferred_date", "message")
        widgets = {
            "name": forms.TextInput(attrs={"autocomplete": "name"}),
            "phone": forms.TextInput(attrs={"type": "tel", "inputmode": "tel", "dir": "ltr", "autocomplete": "tel"}),
            "message": forms.Textarea(attrs={"rows": 4}),
        }

    def __init__(self, *args, kind, **kwargs):
        super().__init__(*args, **kwargs)
        if kind != Inquiry.Kind.VISIT:
            self.fields.pop("preferred_date")
        elif "preferred_date" in self.fields:
            self.fields["preferred_date"].widget.attrs["min"] = date.isoformat(timezone.localdate())

    def clean_phone(self):
        value = normalize_number(self.cleaned_data["phone"])
        value = value.replace(" ", "").replace("-", "")
        digits = value.removeprefix("+")
        if not 8 <= len(digits) <= 15 or not digits.isascii() or not digits.isdecimal():
            raise forms.ValidationError("شماره تماس را به همراه کد شهر یا شماره همراه وارد کنید.")
        return value

    def clean_preferred_date(self):
        value = self.cleaned_data.get("preferred_date")
        if value and value < timezone.localdate():
            raise forms.ValidationError("تاریخ امروز یا یکی از روزهای آینده را انتخاب کنید.")
        return value
