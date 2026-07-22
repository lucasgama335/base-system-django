from .models import UserPermission


def user_can_be_verified(user_obj):
    """
    Checagem-base compartilhada por qualquer verificação de autorização:
    usuário inativo ou soft-deletado nunca possui permissão, independente
    de qual permissão esteja sendo checada.
    """
    return user_obj.is_active and user_obj.deleted_at is None

def user_has_permission(user_obj, code):
    if not user_can_be_verified(user_obj):
        return False
    
    if user_obj.is_superuser:
        return True
    
    return UserPermission.objects.filter(
        user=user_obj, permission__code=code, permission__is_active=True
    ).exists()

def user_permission_codes(user_obj):
    if not user_can_be_verified(user_obj):
        return set()
    
    return set(
        UserPermission.objects.filter(
            user=user_obj, permission__is_active=True
        ).values_list("permission__code", flat=True)
    )