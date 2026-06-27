from django.contrib.auth.models import AbstractUser
from django.db import models

class User(AbstractUser):
    class Roles(models.TextChoices):
        OWNER = "owner", "Owner"
        ADMIN = "admin", "Admin"
        REVIEWER = "reviewer", "Reviewer"

    organization = models.ForeignKey("organizations.Organization", on_delete=models.SET_NULL, null=True, blank=True, related_name="users")
    role = models.CharField(max_length=20, choices=Roles.choices, default=Roles.OWNER)

    def __str__(self):
        return self.email or self.username
