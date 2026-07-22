import base64
import io

import pyotp
import qrcode

from .models import UserBackupCode


def ensure_otp_secret(user):
    """Garante que o usuário tenha um segredo TOTP gerado, sem ativar o 2FA ainda."""
    if not user.otp_secret:
        user.otp_secret = pyotp.random_base32()
        user.save(update_fields=["otp_secret"])

    return user.otp_secret

def build_qr_code_base64(user):
    totp = pyotp.TOTP(user.otp_secret)
    uri = totp.provisioning_uri(name=user.email, issuer_name="SistemaBase")
    img = qrcode.make(uri)
    buffer = io.BytesIO()
    img.save(buffer, format="PNG")

    return base64.b64encode(buffer.getvalue()).decode()

def verify_totp_code(user, code):
    return pyotp.TOTP(user.otp_secret).verify(code)

def activate_2fa(user):
    """Ativa o 2FA e retorna os códigos de backup em texto puro (mostrar 1 única vez)."""
    user.is_2fa_enabled = True
    user.save(update_fields=["is_2fa_enabled"])
    
    return UserBackupCode.generate_codes_for_user(user)

def deactivate_2fa(user):
    UserBackupCode.flush_codes_for_user(user)
    user.otp_secret = None
    user.is_2fa_enabled = False
    user.save(update_fields=["otp_secret", "is_2fa_enabled"])

def verify_second_factor(user, code):
    """Retorna (is_valid, method) onde method é 'totp', 'backup' ou None."""
    if verify_totp_code(user, code):
        return True, "totp"
    
    if UserBackupCode.verify_and_use_code(user, code):
        return True, "backup"
    
    return False, None