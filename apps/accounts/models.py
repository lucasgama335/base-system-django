from django.contrib.auth.base_user import AbstractBaseUser
from django.db import models

from .managers import UserManager


class User(AbstractBaseUser):
    email = models.EmailField(unique=True, max_length=255)
    first_name = models.CharField(max_length=150)
    last_name = models.CharField(max_length=150)
    phone = models.CharField('Telefone', max_length=20, blank=True, null=True)

    is_active = models.BooleanField(default=True)
    is_superuser = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    deleted_at = models.DateTimeField(null=True, blank=True)

    objects = UserManager()

    # Authentication system settings derived from AbstractBaseUser
    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["first_name", "last_name"]

    class Meta:
        db_table = "users"
        verbose_name = "Usuário"
        verbose_name_plural = "Usuários"

    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.email})"
    
    @property
    def is_deleted(self):
        return self.deleted_at is not None

    def soft_delete(self):
        """
        Realiza o soft delete alterando o e-mail para liberar
        o e-mail original para novos cadastros.
        """
        from django.utils import timezone
        now = timezone.now()
        timestamp = int(now.timestamp())
        
        self.deleted_at = now
        self.is_active = False
        # Libera o e-mail original garantindo que a constraint unique=True não seja violada
        self.email = f"{self.email}__deleted_{timestamp}"
        self.save()