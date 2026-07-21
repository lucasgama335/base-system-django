from django.conf import settings
from django.db import models

class Department(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="departments_created",
        verbose_name="Criado por"
    )
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="departments_updated",
        verbose_name="Atualizado por"
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "departments"
        verbose_name = "Departamento"
        verbose_name_plural = "Departamentos"

    def __str__(self):
        return self.name
    
class UserDepartment(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="user_departments",
        verbose_name="Usuário"
    )
    department = models.ForeignKey(
        Department,
        on_delete=models.CASCADE,
        related_name="department_users",
        verbose_name="Departamento"
    )
    granted_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="granted_department_links",
        verbose_name="Concedido por"
    )

    created_at = models.DateTimeField("Criado em", auto_now_add=True)

    class Meta:
        db_table = "user_departments"
        verbose_name = "Departamento do Usuário"
        verbose_name_plural = "Departamentos dos Usuários"
        constraints = [
            models.UniqueConstraint(
                fields=["user", "department"], 
                name="unique_user_department"
            )
        ]
    
    def __str__(self):
        return f"{self.user} → {self.department}"