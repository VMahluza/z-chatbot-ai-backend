from django.db import models
from django.contrib.auth.models import AbstractUser

# Create your models here.
class User(AbstractUser):
    class Role(models.TextChoices):
        ADMIN = "ADMIN", "Admin"
        USER = "USER", "User"
        BOT = "BOT", "Bot"

    # The user will be assumed to be admin on add user
    base_role = Role.ADMIN
    role = models.CharField(max_length=50, choices=Role.choices, default=base_role)

    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.username})"
    

    
