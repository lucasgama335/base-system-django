import re

from django import forms

from apps.accounts.models import User


class PersonalDataForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ["email", "first_name", "last_name", "phone"]
        widgets = {
            "first_name": forms.TextInput(),
            "last_name": forms.TextInput(),
            "email": forms.EmailInput(),
            "phone": forms.TextInput()
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        if self.instance and self.instance.pk:
            
            if self.instance.phone:
                tel = self.instance.phone
                self.initial["phone"] = f'({tel[:2]}) {tel[2:7]}-{tel[7:]}'

    def clean_first_name(self):
        return str(self.cleaned_data["first_name"]).title()

    def clean_last_name(self):
        return str(self.cleaned_data["last_name"]).title()

    def clean_email(self):
        return str(self.cleaned_data["email"]).lower()

    def clean_phone(self):
        masked_phone = self.cleaned_data.get("phone")
        
        if masked_phone:
            cleaned_phone = re.sub(r'[^0-9]', '', masked_phone)
            return cleaned_phone