from django.db import models
from django.conf import settings
from django.contrib.auth.models import AbstractUser

from users.constants import NAME_LENGTH, EMAIL_LENGTH


class FoodgramUser(AbstractUser):
    """
    Пользователь
    """

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ("username", "last_name", "first_name")

    first_name = models.CharField(max_length=NAME_LENGTH, blank=False)
    last_name = models.CharField(max_length=NAME_LENGTH, blank=False)
    email = models.EmailField(max_length=EMAIL_LENGTH, unique=True)
    avatar = models.ImageField(
        upload_to="avatars/",
        null=True,
        blank=True,
        default="default.jpg",
        verbose_name="Аватар пользователя",
    )

    @property
    def avatar_url(self):
        if self.avatar and hasattr(self.avatar, "url"):
            return self.avatar.url
        return getattr(settings, "DEFAULT_AVATAR_URL", None)

    def __str__(self):
        return self.username
