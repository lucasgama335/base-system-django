import secrets

from django.conf import settings
from django.contrib.auth.base_user import AbstractBaseUser
from django.contrib.auth.hashers import check_password, make_password
from django.db import models

from .managers import UserManager


class User(AbstractBaseUser):
    email = models.EmailField(unique=True, max_length=255)
    first_name = models.CharField(max_length=150)
    last_name = models.CharField(max_length=150)
    phone = models.CharField('Telefone', max_length=20, blank=True, null=True)

    is_active = models.BooleanField(default=True)
    is_superuser = models.BooleanField(default=False)

    # Campos para Autenticação em Dois Fatores (2FA)
    otp_secret = models.CharField(max_length=32, blank=True, null=True)
    is_2fa_enabled = models.BooleanField(default=False)

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

class UserBackupCode(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="backup_codes"
    )
    code_hash = models.CharField(max_length=128)
    is_used = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    used_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "user_backup_codes"
        verbose_name = "Código de Backup"
        verbose_name_plural = "Códigos de Backup"

    @classmethod
    def flush_codes_for_user(self, user):
        """
        Invalida códigos antigos.
        """

        self.objects.filter(user=user).delete()
    
    @classmethod
    def generate_codes_for_user(self, user, count=10):
        """
        Invalida códigos antigos, gera N novos códigos em texto puro e 
        salva suas versões criptografadas (hash) no banco de dados.
        Retorna a lista de códigos em texto puro para serem exibidos UMA ÚNICA VEZ.
        """
        # Apaga códigos antigos do usuário por segurança
        self.flush_codes_for_user(user)

        raw_codes = []
        for _ in range(count):
            # Gera um código amigável de 8 caracteres (ex: 4A8F-9K2P)
            part1 = secrets.token_hex(2).upper()
            part2 = secrets.token_hex(2).upper()
            raw_code = f"{part1}-{part2}"
            raw_codes.append(raw_code)

            # Salva o hash no banco
            self.objects.create(
                user=user,
                code_hash=make_password(raw_code)
            )

        return raw_codes

    @classmethod
    def verify_and_use_code(self, user, raw_code):
        """
        Verifica se o código em texto puro informado pertence a algum código 
        não utilizado do usuário. Se válido, marca como utilizado.
        """
        cleaned_code = raw_code.strip().upper()
        active_codes = self.objects.filter(user=user, is_used=False)

        for backup_code in active_codes:
            if check_password(cleaned_code, backup_code.code_hash):
                from django.utils import timezone
                backup_code.is_used = True
                backup_code.used_at = timezone.now()
                backup_code.save(update_fields=['is_used', 'used_at'])
                return True

        return False