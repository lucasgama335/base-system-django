from django import forms
from django_recaptcha.fields import ReCaptchaField
from django_recaptcha.widgets import ReCaptchaV3


class LoginForm(forms.Form):
    email = forms.EmailField(
        label="E-mail", 
        required=True, 
        max_length=255,
        widget=forms.EmailInput(attrs={
            "placeholder": "seu@email.com",
            "autofocus": True
        })
    )
    password = forms.CharField(
        label="Senha",
        widget=forms.PasswordInput(attrs={
            "placeholder": "••••••••"
        })
    )
    remember_me = forms.BooleanField(
        required=False, 
        label="Lembrar de mim neste dispositivo",
        widget=forms.CheckboxInput()
    )

    captcha = ReCaptchaField(widget=ReCaptchaV3(
        required_score=0.85,
        action='signin'
    ))