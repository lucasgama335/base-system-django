import base64
import io

import pyotp
import qrcode
from django.conf import settings
from django.contrib import messages
from django.contrib.auth import login, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render
from django.views.decorators.http import require_POST
from django_ratelimit.decorators import ratelimit

from apps.accounts.models import User, UserBackupCode
from apps.accounts.utils import get_ratelimit_ip, update_user_remember_session


@login_required
@ratelimit(key=get_ratelimit_ip, rate="5/m", method="POST", block=True)
def setup_2fa_view(request):
    user = request.user

    # Se o 2FA já estiver ativo, não há necessidade de reconfigurar
    if user.is_2fa_enabled:
        messages.info(request, "A autenticação em dois fatores (2FA) já está ativada na sua conta.")
        return redirect("core:dashboard")

    # 1. Se o usuário ainda não possui uma chave secreta temporária, geramos uma
    if not user.otp_secret:
        user.otp_secret = pyotp.random_base32()
        user.save(update_fields=["otp_secret"])

    totp = pyotp.TOTP(user.otp_secret)

    # 2. Processa a confirmação do código digitado pelo usuário
    if request.method == 'POST':
        code = request.POST.get("code", "").strip()

        # Valida o código de 6 dígitos fornecido pelo app (Authenticator)
        if totp.verify(code):
            user.is_2fa_enabled = True
            user.save(update_fields=['is_2fa_enabled'])

            # Atualiza a chave de sessão do usuário atual e invalida o login em todos os outros navegadores/dispositivos
            update_session_auth_hash(request, user)

            # --- GERAR CÓDIGOS DE BACKUP ---
            raw_backup_codes = UserBackupCode.generate_codes_for_user(user)

            messages.success(request, "2FA ativado com sucesso! Sua conta está mais segura.")
            return render(request, "accounts/authentication/2fa_backup_codes_show.html", {
                "backup_codes": raw_backup_codes
            })
        else:
            messages.error(request, "Código de verificação inválido. Tente novamente.")

    # 3. Gera o Link URI do TOTP (usado pelos apps de autenticação)
    provisioning_uri = totp.provisioning_uri(
        name=user.email,
        issuer_name="SistemaBase"  # Nome que aparecerá no app do usuário
    )

    # 4. Converte o QR Code em imagem PNG codificada em Base64
    img = qrcode.make(provisioning_uri)
    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    qr_code_base64 = base64.b64encode(buffer.getvalue()).decode()

    context = {
        "qr_code_base64": qr_code_base64,
        "secret_key": user.otp_secret,
    }
    return render(request, "accounts/authentication/2fa_setup.html", context)

@ratelimit(key=get_ratelimit_ip, rate="5/m", method="POST", block=True)
def verify_2fa_view(request):
    # Se o usuário já estiver logado, não precisa estar aqui
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
        totp = pyotp.TOTP(user.otp_secret)

        # 1. Tenta validar via TOTP (6 dígitos)
        is_totp_valid = totp.verify(code)

        # 2. Se o TOTP falhou, tenta validar como Código de Backup
        is_backup_valid = False
        if not is_totp_valid:
            is_backup_valid = UserBackupCode.verify_and_use_code(user, code)

        if is_totp_valid or is_backup_valid:
            # Autentica oficialmente o usuário no Django
            login(request, user, "apps.accounts.backends.EmailAuthenticationBackend")
            update_user_remember_session(request, remember_me)

            # Limpa as variáveis temporárias da sessão por segurança
            del request.session['pre_2fa_user_id']
            if 'pre_2fa_remember_me' in request.session:
                del request.session['pre_2fa_remember_me']

            if is_backup_valid:
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
    print(user.is_2fa_enabled)
    if user.is_2fa_enabled:
        UserBackupCode.flush_codes_for_user(user)
        user.otp_secret = None
        user.is_2fa_enabled = False
        messages.success(request, "Autenticação em Dois Fatores Desativada!")
        user.save(update_fields=["otp_secret", "is_2fa_enabled"])

    else:
        return redirect("accounts:2fa_setup")

    return redirect(settings.LOGIN_REDIRECT_URL)