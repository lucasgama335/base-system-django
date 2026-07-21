from django.contrib.auth.base_user import BaseUserManager

class UserManager(BaseUserManager):
    """
    Manager para criação de usuários com e-mail como chave de login.
    """
    def get_queryset(self):
        # Exclui usuários soft-deletados por padrão em qualquer consulta
        return super().get_queryset().filter(deleted_at__isnull=True)

    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError("O e-mail é obrigatório.")
        
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("is_active", True)

        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser precisa ter is_superuser=True.")

        return self.create_user(email, password, **extra_fields)