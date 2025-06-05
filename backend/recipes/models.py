"""
Основные модели базы данных
"""

from django.contrib.auth import get_user_model
from django.db import models, IntegrityError
from django.urls import reverse
from django.utils.crypto import get_random_string
from django.db.models import Q, F

from recipes.contsants import (
    INGREDIENT_NAME_LENGTH,
    MEASUREMENT_LENGTH,
    RECIPE_NAME_LENGTH,
    CODE_LENGTH,
    COUNT_TRY,
)

User = get_user_model()


class Ingredient(models.Model):
    """
    Ингредиент
    """

    name = models.CharField(max_length=INGREDIENT_NAME_LENGTH, verbose_name="Название")
    measurement_unit = models.CharField(
        max_length=MEASUREMENT_LENGTH, verbose_name="Единица измерения"
    )

    class Meta:
        verbose_name = "Ингредиент"
        verbose_name_plural = "Ингредиенты"
        ordering = ["name"]
        constraints = [
            models.UniqueConstraint(
                fields=["name", "measurement_unit"],
                name="unique_ingredient_name_measurement_unit",
            )
        ]

    def __str__(self):
        return f"{self.name} ({self.measurement_unit})"


class Recipe(models.Model):
    """
    Рецепт
    """

    author = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="recipes", verbose_name="Автор"
    )
    name = models.CharField(max_length=RECIPE_NAME_LENGTH, verbose_name="Название")
    text = models.TextField(verbose_name="Описание")
    image = models.ImageField(upload_to="recipes/images/", verbose_name="Картинка")
    cooking_time = models.PositiveIntegerField(verbose_name="Время приготовления (мин)")

    class Meta:
        verbose_name = "Рецепт"
        verbose_name_plural = "Рецепты"
        ordering = ["-id"]

    def __str__(self):
        return self.name


class RecipeIngredient(models.Model):
    """
    Количество ингредиента в конкретном рецепте
    """

    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name="ingredient_links",
        verbose_name="Рецепт",
    )
    ingredient = models.ForeignKey(
        Ingredient,
        on_delete=models.CASCADE,
        related_name="recipe_links",
        verbose_name="Ингредиент",
    )
    amount = models.PositiveIntegerField(verbose_name="Количество")

    class Meta:
        verbose_name = "Ингредиент в рецепте"
        verbose_name_plural = "Ингредиенты в рецептах"
        constraints = [
            models.UniqueConstraint(
                fields=["recipe", "ingredient"], name="unique_recipe_ingredient"
            )
        ]

    def __str__(self):
        return (
            f"{self.ingredient.name} — {self.amount}{self.ingredient.measurement_unit}"
        )


class Favorite(models.Model):
    """
    Избранное: связь пользователь–рецепт
    """

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="favorite",
        verbose_name="Пользователь",
    )
    recipe = models.ForeignKey(
        Recipe, on_delete=models.CASCADE, related_name="favorite", verbose_name="Рецепт"
    )
    added_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата добавления")

    class Meta:
        verbose_name = "Избранное"
        verbose_name_plural = "Избранные рецепты"
        constraints = [
            models.UniqueConstraint(
                fields=["user", "recipe"], name="unique_favorite_user_recipe"
            )
        ]

    def __str__(self):
        return f"{self.user.username} -> {self.recipe.name}"


class ShoppingCart(models.Model):
    """
    Список покупок: связь пользователь–рецепт
    """

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="shopping_carts",
        verbose_name="Пользователь",
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name="shoppingcart",
        verbose_name="Рецепт",
    )
    added_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата добавления")

    class Meta:
        verbose_name = "Корзина покупок"
        verbose_name_plural = "Корзины покупок"
        constraints = [
            models.UniqueConstraint(
                fields=["user", "recipe"], name="unique_cart_user_recipe"
            )
        ]

    def __str__(self):
        return f"{self.user.username} — {self.recipe.name}"


class Subscription(models.Model):
    """
    Подписка пользователя на автора
    """

    subscriber = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="subscription_links",
        verbose_name="Подписчик",
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="follower_links",
        verbose_name="Автор",
    )
    subscribed_at = models.DateTimeField(
        auto_now_add=True, verbose_name="Дата подписки"
    )

    class Meta:
        verbose_name = "Подписка"
        verbose_name_plural = "Подписки"
        constraints = [
            models.UniqueConstraint(
                fields=["subscriber", "author"],
                name="unique_subscription_subscriber_author",
            ),
            models.CheckConstraint(
                check=~Q(subscriber=F("author")),
                name="prevent_self_subscription",
            ),
        ]

    def __str__(self):
        return f"{self.subscriber.username} -> {self.author.username}"


class ShortLink(models.Model):
    """
    Короткая ссылка на рецепт
    """

    recipe = models.OneToOneField(
        Recipe,
        on_delete=models.CASCADE,
        related_name="short_link",
        verbose_name="Рецепт",
    )
    code = models.SlugField(
        max_length=CODE_LENGTH, unique=True, editable=False, verbose_name="Код"
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")

    class Meta:
        verbose_name = "Короткая ссылка"
        verbose_name_plural = "Короткие ссылки"

    def save(self, *args, **kwargs):
        if not self.code:
            for _ in range(COUNT_TRY):
                code = get_random_string(CODE_LENGTH)
                if not ShortLink.objects.filter(code=code).exists():
                    self.code = code
                    break
            else:
                raise IntegrityError("Не удалось сгенерировать уникальный код")
        super().save(*args, **kwargs)

    def __str__(self):
        return self.code

    def get_short_url(self):
        return reverse("recipes:shortlink-redirect", args=[self.code])
