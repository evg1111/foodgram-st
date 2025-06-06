from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from users.models import FoodgramUser


@admin.register(FoodgramUser)
class FoodgramUserAdmin(UserAdmin):
    """Админка для кастомного пользователя"""

    fieldsets = UserAdmin.fieldsets + (("Дополнительно", {"fields": ("avatar",)}),)
    list_display = ("username", "email", "first_name", "last_name", "is_staff")
    search_fields = ("username", "email", "first_name", "last_name")
