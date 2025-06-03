from django.db import models
from django.conf import settings
from django.contrib.auth.models import AbstractUser


class CustomUser(AbstractUser):
    """
    Пользователь
    """
    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ("username", "last_name", "first_name")

    first_name = models.CharField(max_length=150, blank=False)
    last_name = models.CharField(max_length=150, blank=False)
    email = models.EmailField(unique=True)
    avatar = models.ImageField(
        upload_to='avatars/',
        null=True,
        blank=True,
        default='default.jpg',
        verbose_name='Аватар пользователя'
    )

    # Подписки: кто на кого подписан
    subscriptions = models.ManyToManyField(
        'self',
        through='Subscription',
        symmetrical=False,
        related_name='subscribers',
        verbose_name='Подписки'
    )

    @property
    def avatar_url(self):
        if self.avatar and hasattr(self.avatar, 'url'):
            return self.avatar.url
        return getattr(settings, 'DEFAULT_AVATAR_URL', None)

    def __str__(self):
        return self.username
