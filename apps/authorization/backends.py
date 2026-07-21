from django.contrib.auth.backends import BaseBackend
from .models import UserPermission

def _user_can_be_verified(user_obj):
    """
    Checagem-base compartilhada por qualquer verificação de autorização:
    usuário inativo ou soft-deletado nunca possui permissão, independente
    de qual permissão esteja sendo checada.
    """
    return user_obj.is_active and user_obj.deleted_at is None

class CustomAuthorizationBackend(BaseBackend):
    """
    Backend customizado para resolver permissões do usuário 
    através da tabela customizada UserPermission.
    """
        
    def has_perm(self, user_obj, perm, obj=None):
        # 1. Usuários inativos ou deletados não possuem permissões
        if not _user_can_be_verified(user_obj):
            return False
        
        # 2. Superusuários têm acesso irrestrito
        if user_obj.is_superuser:
            return True
        
        # 3. Consulta no banco se o usuário possui a permissão ativa
        return UserPermission.objects.filter(
            user=user_obj,
            permission__code=perm,
            permission__is_active=True
        ).exists()
    
    def get_all_permissions(self, user_obj, obj=None):
        """
        Retorna o conjunto de códigos de permissões ativas do usuário.

        Superusuários NÃO recebem um bypass aqui, ao contrário de has_perm():
        a lista real de permissões de um superusuário é intencionalmente vazia
        (ele tem acesso irrestrito por is_superuser, não por permissões
        nomeadas). Não usar esse método pra decidir o que exibir num menu
        achando que ele reflete o acesso real do usuário — use has_perm()
        pra isso.
        """
        if not _user_can_be_verified(user_obj):
            return set()
        
        return set(
            UserPermission.objects.filter(
                user=user_obj,
                permission__is_active=True
            ).values_list("permission__code", flat=True)
        )