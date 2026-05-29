from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    class Meta:
        db_table = "users"


class Role(models.Model):
    role_id = models.BigAutoField(primary_key=True, db_column="role_id")
    role_name = models.CharField(max_length=50, unique=True)
    description = models.TextField(blank=True)
    status = models.CharField(max_length=20, default="Active")

    class Meta:
        db_table = "roles"
        ordering = ["role_name"]

    def __str__(self):
        return self.role_name


class UserRole(models.Model):
    user_role_id = models.BigAutoField(primary_key=True, db_column="user_role_id")
    user = models.ForeignKey(User, on_delete=models.CASCADE, db_column="user_id", related_name="user_roles")
    role = models.ForeignKey(Role, on_delete=models.CASCADE, db_column="role_id", related_name="user_roles")

    class Meta:
        db_table = "user_roles"
        ordering = ["user_id", "role_id"]
        constraints = [
            models.UniqueConstraint(fields=["user", "role"], name="uniq_user_role")
        ]

        

    def __str__(self):
        return f"{self.user} - {self.role}"













