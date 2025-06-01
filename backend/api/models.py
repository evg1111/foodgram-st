"""
Основные модели базы данных
"""
from django.conf import settings
from django.db import models, IntegrityError
from django.contrib.auth.models import AbstractUser
from django.urls import reverse
from django.utils.crypto import get_random_string


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


class Ingredient(models.Model):
    """
    Ингредиент
    """
    name = models.CharField(max_length=128, verbose_name='Название')
    measurement_unit = models.CharField(max_length=64, verbose_name='Единица измерения')

    class Meta:
        verbose_name = 'Ингредиент'
        verbose_name_plural = 'Ингредиенты'
        ordering = ['name']
        unique_together = ('name', 'measurement_unit')

    def __str__(self):
        return f"{self.name} ({self.measurement_unit})"


class Recipe(models.Model):
    """
    Рецепт
    """
    author = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='recipes',
        verbose_name='Автор'
    )
    name = models.CharField(max_length=256, verbose_name='Название')
    text = models.TextField(verbose_name='Описание')
    image = models.ImageField(upload_to='recipes/images/', verbose_name='Картинка')
    cooking_time = models.PositiveIntegerField(verbose_name='Время приготовления (мин)')
    ingredients = models.ManyToManyField(
        Ingredient,
        through='RecipeIngredient',
        related_name='recipes',
        verbose_name='Ингредиенты'
    )
    favorited_by = models.ManyToManyField(
        CustomUser,
        through='Favorite',
        related_name='favorite_recipes',
        verbose_name='Добавили в избранное'
    )
    in_shopping_cart = models.ManyToManyField(
        CustomUser,
        through='ShoppingCart',
        related_name='cart_recipes',
        verbose_name='В корзине'
    )

    class Meta:
        verbose_name = 'Рецепт'
        verbose_name_plural = 'Рецепты'
        ordering = ['-id']

    def __str__(self):
        return self.name


class RecipeIngredient(models.Model):
    """
    Количество ингредиента в конкретном рецепте
    """
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='ingredient_links'
    )
    ingredient = models.ForeignKey(
        Ingredient,
        on_delete=models.CASCADE,
        related_name='recipe_links'
    )
    amount = models.PositiveIntegerField(verbose_name='Количество')

    class Meta:
        verbose_name = 'Ингредиент в рецепте'
        verbose_name_plural = 'Ингредиенты в рецептах'
        unique_together = ('recipe', 'ingredient')

    def __str__(self):
        return f"{self.ingredient.name} — {self.amount}{self.ingredient.measurement_unit}"


class Favorite(models.Model):
    """
    Избранное: связь пользователь–рецепт
    """
    user = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='favorite'
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='favorite'
    )
    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Избранное'
        verbose_name_plural = 'Избранные рецепты'
        unique_together = ('user', 'recipe')

    def __str__(self):
        return f"{self.user.username} -> {self.recipe.name}"


class ShoppingCart(models.Model):
    """
    Список покупок: связь пользователь–рецепт
    """
    user = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='shopping_carts'
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='shoppingcart'
    )
    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Корзина покупок'
        verbose_name_plural = 'Корзины покупок'
        unique_together = ('user', 'recipe')

    def __str__(self):
        return f"{self.user.username} — {self.recipe.name}"


class Subscription(models.Model):
    """
    Подписка пользователя на автора
    """
    subscriber = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='subscription_links'
    )
    author = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='follower_links'
    )
    subscribed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Подписка'
        verbose_name_plural = 'Подписки'
        unique_together = ('subscriber', 'author')

    def __str__(self):
        return f"{self.subscriber.username} -> {self.author.username}"


def generate_short_code():
    return get_random_string(8)


class ShortLink(models.Model):
    """
    Короткая ссылка на рецепт
    """
    recipe = models.OneToOneField(
        Recipe,
        on_delete=models.CASCADE,
        related_name='short_link'
    )
    code = models.SlugField(
        max_length=10,
        unique=True,
        default=generate_short_code,
        editable=False
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Короткая ссылка'
        verbose_name_plural = 'Короткие ссылки'

    def save(self, *args, **kwargs):
        if not self.code:
            for _ in range(15):
                code = get_random_string(8)
                if not ShortLink.objects.filter(code=code).exists():
                    self.code = code
                    break
            else:
                raise IntegrityError("Не удалось сгенерировать уникальный код")
        super().save(*args, **kwargs)

    def __str__(self):
        return self.code

    def get_short_url(self):
        return reverse('shortlink-redirect', args=[self.code])