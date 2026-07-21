from django.conf import settings
from django.db import models


class Permission(models.Model):
    code = models.CharField(max_length=100, unique=True, db_index=True)
    name = models.CharField(max_length=150)
    description = models.TextField(blank=True, null=True)
    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "permissions"
        verbose_name = "Permissão"
        verbose_name_plural = "Permissões"

    def __str__(self):
        return f"{self.name} ({self.code})"
    
class UserPermission(models.Model):
    class SourceType(models.TextChoices):
        MANUAL = "manual", "Manual"
        DEPARTMENT = "department", "Departamento"

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name="permission_links",
        on_delete=models.CASCADE,
    )
    permission = models.ForeignKey(
        Permission,
        related_name="user_links",
        on_delete=models.CASCADE,
    )

    source = models.CharField(
        max_length=20,
        choices=SourceType.choices,
        default=SourceType.MANUAL,
    )
    origin_department = models.ForeignKey(
        "departments.Department",
        related_name="granted_permissions",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    granted_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name="permission_links_granted",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "user_permissions"
        verbose_name = "Permissão do Usuário"
        verbose_name_plural = "Permissões dos Usuários"
        constraints = [
            models.UniqueConstraint(
                fields=["user", "permission"],
                name="unique_user_permission",
            )
        ]
    
    def __str__(self):
        return f"{self.user} → {self.permission}"
    
class DepartmentPermissionTemplate(models.Model):
    department = models.ForeignKey(
        "departments.Department",
        on_delete=models.CASCADE,
        related_name="permission_templates",
        verbose_name="Departamento"
    )
    permission = models.ForeignKey(
        Permission,
        on_delete=models.CASCADE,
        related_name="department_templates",
        verbose_name="Permissão"
    )

    created_at = models.DateTimeField('Criado em', auto_now_add=True)

    class Meta:
        db_table = 'department_permission_templates'
        verbose_name = "Template de Permissão do Departamento"
        verbose_name_plural = "Templates de Permissões dos Departamentos"
        constraints = [
            models.UniqueConstraint(
                fields=["department", "permission"],
                name="unique_department_permission_template",
            )
        ]
    
    def __str__(self):
        return f"{self.department} → {self.permission}"