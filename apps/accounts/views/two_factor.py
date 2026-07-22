from django.conf import settings
from django.contrib import messages
from django.contrib.auth import login, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render
from django.views.decorators.http import require_POST
from django_ratelimit.decorators import ratelimit

from apps.accounts import services
from apps.accounts.models import User, UserBackupCode
from apps.accounts.utils import apply_session_expiry, get_ratelimit_ip


@login_required
@ratelimit(key=get_ratelimit_ip, rate="5/m", method="POST", block=True)
def setup_2fa_view(request):
    user = request.user
    if user.is_2fa_enabled:
        messages.info(request, "A autenticação em dois fatores (2FA) já está ativada na sua conta.")
        return redirect("core:dashboard")

    services.ensure_otp_secret(user)

    if request.method == 'POST':
        code = request.POST.get("code", "").strip()
        if services.verify_totp_code(user, code):
            raw_codes = services.activate_2fa(user)
            update_session_auth_hash(request, user)
            messages.success(request, "2FA ativado com sucesso! Sua conta está mais segura.")
            return render(request, "accounts/authentication/2fa_backup_codes_show.html", { "backup_codes": raw_codes })
        else:
            messages.error(request, "Código de verificação inválido. Tente novamente.")

    context = {
        "qr_code_base64": services.build_qr_code_base64(user),
        "secret_key": user.otp_secret,
    }
    return render(request, "accounts/authentication/2fa_setup.html", context)

@ratelimit(key=get_ratelimit_ip, rate="5/m", method="POST", block=True)
def verify_2fa_view(request):
    if request.user.is_authenticated:
        return redirect(settings.LOGIN_REDIRECT_URL)

    # Recupera o ID do usuário que passou pela 1ª etapa (e-mail + senha)
    user_id = request.session.get("pre_2fa_user_id")
    remember_me = request.session.get("pre_2fa_remember_me", False)

    # Proteção: Se alguém tentar acessar a URL diretamente sem passar pelo login
    if not user_id:
        messages.error(request, "Sessão expirada ou inválida. Faça login novamente.")
        return redirect(settings.LOGIN_URL)

    try:
        user = User.objects.get(pk=user_id)
    except User.DoesNotExist:
        messages.error(request, "Usuário não encontrado.")
        return redirect(settings.LOGIN_URL)

    if request.method == "POST":
        code = request.POST.get("code", "").strip()

        is_valid, method = services.verify_second_factor(user, code)
        if is_valid:
            # Autentica oficialmente o usuário no Django
            login(request, user, "apps.accounts.backends.EmailAuthenticationBackend")
            apply_session_expiry(request, remember_me)

            # Limpa as variáveis temporárias da sessão por segurança
            del request.session['pre_2fa_user_id']
            if 'pre_2fa_remember_me' in request.session:
                del request.session['pre_2fa_remember_me']

            if method == "backup":
                messages.warning(request, "Você utilizou um código de backup para entrar. Lembre-se de que ele não poderá ser reusado.")
            else:
                messages.success(request, f"Bem-vindo(a) de volta, { user.first_name or user.email }!")
            return redirect(settings.LOGIN_REDIRECT_URL)
        else:
            messages.error(request, "Código de autenticação inválido. Tente novamente.")

    return render(request, "accounts/authentication/2fa_verify.html", { "user_email": user.email })

@login_required
@require_POST
def switch_2fa_view(request):
    user = request.user
    if user.is_2fa_enabled:
        services.deactivate_2fa(user)
        messages.success(request, "Autenticação em Dois Fatores Desativada!")
    else:
        return redirect("accounts:2fa_setup")
    return redirect(settings.LOGIN_REDIRECT_URL)