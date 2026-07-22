from django.conf import settings
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.views import (
    PasswordResetCompleteView,
    PasswordResetConfirmView,
    PasswordResetDoneView,
    PasswordResetView,
)
from django.shortcuts import redirect, render
from django.urls import reverse_lazy
from django.views.decorators.http import require_POST
from django_ratelimit.decorators import ratelimit

from apps.accounts.forms import LoginForm
from apps.accounts.utils import get_ratelimit_ip, redirect_safe_next_url


@ratelimit(key=get_ratelimit_ip, rate="5/m", method="POST", block=True)
def login_view(request):   
    if request.user.is_authenticated:
        return redirect(settings.LOGIN_REDIRECT_URL)
    
    if request.method == "POST":
        form = LoginForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data["email"]
            password = form.cleaned_data["password"]
            remember_me = form.cleaned_data["remember_me"]

            user = authenticate(request,  email=email, password=password)

            if user is not None:
                # --- INTERCEPTAÇÃO DO 2FA ---
                if user.is_2fa_enabled:
                    # Salva temporariamente os dados na sessão sem autenticar o usuário ainda
                    request.session['pre_2fa_user_id'] = user.id
                    request.session['pre_2fa_remember_me'] = remember_me
                    return redirect('accounts:2fa_verify')
                
                # --- LOGIN NORMAL (SEM 2FA) ---
                login(request, user)

                if remember_me:
                    request.session.set_expiry(14 * 24 * 60 * 60)
                else:
                    request.session.set_expiry(0)

                return redirect_safe_next_url(request, settings.LOGIN_REDIRECT_URL)
            else:
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