from django.contrib.auth.backends import BaseBackend
from apps.accounts.models import User

class EmailAuthenticationBackend(BaseBackend):
    """
    Backend essencial para autenticar usuários via E-mail e Senha.
    """
    def authenticate(self, request, email=None, password=None, **kwargs):
        if not email or not password:
            return None

        try:
            # Busca apenas usuários que não foram soft-deleted
            user = User.objects.get(email=email, deleted_at__isnull=True)
            if user.check_password(password) and user.is_active:
                return user
            
        except User.DoesNotExist:
            # Proteção contra Timing Attacks (simula o tempo de hash da senha)
            User().set_password(password)
            return None
    
    def get_user(self, user_id):
        try:
            return User.objects.get(pk=user_id, deleted_at__isnull=True)
        except User.DoesNotExist:
            return None