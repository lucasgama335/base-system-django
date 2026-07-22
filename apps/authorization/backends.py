from django.contrib.auth.backends import BaseBackend

from . import services


class CustomAuthorizationBackend(BaseBackend):
    """
    Backend customizado para resolver permissões do usuário 
    através da tabela customizada UserPermission.
    """
        
    def has_perm(self, user_obj, perm, obj=None):
        return services.user_has_permission(user_obj, perm)

    def get_all_permissions(self, user_obj, obj=None):
        return services.user_permission_codes(user_obj)