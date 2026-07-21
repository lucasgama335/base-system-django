from django import forms

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