from django.shortcuts import redirect, render
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.views import (PasswordResetDoneView, PasswordResetConfirmView, PasswordResetCompleteView, PasswordResetView)
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.http import require_POST
from django.urls import reverse_lazy
from django.conf import settings
from apps.accounts.forms import LoginForm

def login_view(request):   
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

@require_POST
def logout_view(request):
    """
    Encerra a sessão do usuário com segurança e redireciona para o login.
    """
    # Encerra a sessão, apaga o cookie e o registro no banco
    logout(request)

    # Exibe uma mensagem amigável
    messages.info(request, "Você saiu do sistema com sucesso.")

    # Redireciona para a tela de login
    return redirect(settings.LOGIN_URL)

class PasswordResetView(PasswordResetView):
    template_name = "accounts/authentication/password_reset.html"
    email_template_name = "accounts/emails/password_reset_email.html"
    subject_template_name = "accounts/emails/password_reset_subject.txt"
    success_url = reverse_lazy("accounts:password_reset_done")

class PasswordResetDoneView(PasswordResetDoneView):
    template_name = "accounts/authentication/password_reset_done.html"

class PasswordResetConfirmView(PasswordResetConfirmView):
    template_name = "accounts/authentication/password_reset_confirm.html"
    success_url = reverse_lazy("accounts:password_reset_complete")

class PasswordResetCompleteView(PasswordResetCompleteView):
    template_name = "accounts/authentication/password_reset_complete.html"