from django.shortcuts import redirect, render
from django.contrib.auth import authenticate, login, logout
from django.views.decorators.http import require_POST
from django.contrib import messages
from apps.accounts.forms import LoginForm
from django.conf import settings

def login_view(request):   
    # 1. Guarda de autenticação
    if request.user.is_authenticated:
        return redirect(settings.LOGIN_REDIRECT_URL)
    if request.method == "POST":
        form = LoginForm(request.POST)
        if form.is_valid():
            user = authenticate(
                request, 
                email=form.cleaned_data["email"],
                password=form.cleaned_data["password"]
            )
            if user:
                login(request, user)
                next_url = request.GET.get("next", settings.LOGIN_REDIRECT_URL)
                return redirect(next_url)
            
            messages.error(request, "E-mail e ou senha inválidos.")
    else:
        form = LoginForm()
    return render(request, "accounts/authentication/login.html", {
        "form": form
    })

def register_view(request):
    if request.user.is_authenticated:
        return redirect(settings.LOGIN_REDIRECT_URL)
    
    return render(request, "accounts/authentication/register.html")

def password_recovery_view(request):
    if request.user.is_authenticated:
        return redirect(settings.LOGIN_REDIRECT_URL)
    
    return render(request, "accounts/authentication/recovery_password.html")

@require_POST
def logout_view(request):
    logout(request)
    return redirect(settings.LOGIN_URL)