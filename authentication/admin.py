from django.contrib import admin
from django.contrib.auth import get_user_model

# Register your models here.
class UserAdmin(admin.ModelAdmin):
    list_display = ("id", "username", "email", "is_staff", "is_superuser", "is_active", "last_login", "date_joined")
    search_fields = ("username", "email")
    list_filter = ("is_staff", "is_superuser", "is_active")
    ordering = ("id",)

User = get_user_model()
admin.site.register(User, UserAdmin)