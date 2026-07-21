from django.shortcuts import redirect, render
from django.contrib.auth import authenticate, login, logout
from django.views.decorators.http import require_POST
from django.utils.http import url_has_allowed_host_and_scheme
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
            if user is not None:
                login(request, user)
                if form.cleaned_data["remember_me"]:
                    request.session.set_expiry(14 * 24 * 60 * 60)
                else:
                    request.session.set_expiry(0)

                # Redireciona o usuário para a url que ele estava tentando entrar ou caso seja inválida para a url da dashboard    
                next_url = request.GET.get("next")
                if next_url and url_has_allowed_host_and_scheme(
                    url=next_url,
                    allowed_hosts={request.get_host()},
                    require_https=request.is_secure()
                ):
                    return redirect(next_url)
                
                return redirect(settings.LOGIN_REDIRECT_URL)
            
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