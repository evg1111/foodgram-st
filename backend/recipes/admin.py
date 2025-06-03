"""
Настройки админ-панели для моделей
"""
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import (
    CustomUser, Ingredient, Recipe, RecipeIngredient,
    Favorite, ShoppingCart, Subscription, ShortLink
)


class RecipeIngredientInline(admin.TabularInline):
    model = RecipeIngredient
    extra = 1




@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    """Админка для ингредиентов"""
    list_display = ('name', 'measurement_unit')
    search_fields = ('name',)


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    """Админка для рецептов"""
    list_display = ('name', 'author', 'cooking_time')
    list_filter = ('author',)
    search_fields = ('name', 'author__username')
    inlines = (RecipeIngredientInline,)


@admin.register(Favorite)
class FavoriteAdmin(admin.ModelAdmin):
    """Админка для избранного"""
    list_display = ('user', 'recipe', 'added_at')
    list_filter = ('added_at',)
    search_fields = ('user__username', 'recipe__name')


@admin.register(ShoppingCart)
class ShoppingCartAdmin(admin.ModelAdmin):
    """Админка для корзины покупок"""
    list_display = ('user', 'recipe', 'added_at')
    list_filter = ('added_at',)
    search_fields = ('user__username', 'recipe__name')


@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    """Админка для подписок"""
    list_display = ('subscriber', 'author', 'subscribed_at')
    list_filter = ('subscribed_at',)
    search_fields = ('subscriber__username', 'author__username')


@admin.register(ShortLink)
class ShortLinkAdmin(admin.ModelAdmin):
    """Админка для коротких ссылок"""
    list_display = ('recipe', 'code', 'created_at')
    search_fields = ('code', 'recipe__name')
