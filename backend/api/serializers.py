from rest_framework import serializers
from django.contrib.auth import get_user_model
from drf_extra_fields.fields import Base64ImageField

from api.constants import MIN_COOKING_TIME
from recipes.models import (
    Ingredient, Recipe, RecipeIngredient,
    Favorite, ShoppingCart, Subscription, ShortLink
)

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    is_subscribed = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ('id', 'email', 'username', 'first_name', 'last_name', 'is_subscribed', 'avatar')

    def get_is_subscribed(self, obj):
        request = self.context.get('request')
        if not request or request.user.is_anonymous:
            return False
        return Subscription.objects.filter(subscriber=request.user, author=obj).exists()


class CustomUserCreateSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ('id', 'email', 'username', 'first_name', 'last_name', 'password')

    def create(self, validated_data):
        user = User(
            email=validated_data['email'],
            username=validated_data['username'],
            first_name=validated_data['first_name'],
            last_name=validated_data['last_name'],
        )
        user.set_password(validated_data['password'])
        user.save()
        return user


class CustomUserResponseSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'email', 'username', 'first_name', 'last_name')


class IngredientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ingredient
        fields = ('id', 'name', 'measurement_unit')


class RecipeMinifiedSerializer(serializers.ModelSerializer):
    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time')


class IngredientWriteSerializer(serializers.Serializer):
    id = serializers.PrimaryKeyRelatedField(
        queryset=Ingredient.objects.all(),
        source='ingredient',
        write_only=True,
    )
    amount = serializers.IntegerField()


class IngredientReadSerializer(serializers.ModelSerializer):
    id = serializers.ReadOnlyField(source='ingredient.id')
    name = serializers.ReadOnlyField(source='ingredient.name')
    measurement_unit = serializers.ReadOnlyField(source='ingredient.measurement_unit')

    class Meta:
        model = RecipeIngredient
        fields = ('id', 'name', 'measurement_unit', 'amount')


class RecipeSerializer(serializers.ModelSerializer):
    author = UserSerializer(read_only=True)
    ingredients = IngredientReadSerializer(many=True, source='ingredient_links')
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()

    class Meta:
        model = Recipe
        fields = (
            'id', 'author', 'ingredients', 'is_favorited', 'is_in_shopping_cart',
            'name', 'image', 'text', 'cooking_time'
        )

    def get_is_favorited(self, obj):
        user = self.context['request'].user
        if user.is_anonymous:
            return False
        return Favorite.objects.filter(user=user, recipe=obj).exists()

    def get_is_in_shopping_cart(self, obj):
        user = self.context['request'].user
        if user.is_anonymous:
            return False
        return ShoppingCart.objects.filter(user=user, recipe=obj).exists()


class RecipeCreateUpdateSerializer(serializers.ModelSerializer):
    ingredients = IngredientWriteSerializer(
        many=True,
        required=True,
        allow_empty=False,
    )
    image = Base64ImageField()

    class Meta:
        model = Recipe
        fields = ('ingredients', 'image', 'name', 'text', 'cooking_time')

    def to_representation(self, instance):
        return RecipeSerializer(instance, context=self.context).data

    def validate_image(self, value):
        if not value:
            raise serializers.ValidationError('Нужно указать фото.')
        return value

    def validate_cooking_time(self, value):
        if value < MIN_COOKING_TIME:
            raise serializers.ValidationError(
                f'Время приготовления должно быть не меньше {MIN_COOKING_TIME}.'
            )
        return value

    def validate_ingredients(self, value):
        if not value:
            raise serializers.ValidationError('Нужно указать хотя бы один ингредиент.')
        seen_ids = set()
        for item in value:
            ingredient_id = item.get('ingredient')
            amount = item.get('amount')
            # Проверяем наличие id и amount
            if ingredient_id is None:
                raise serializers.ValidationError('Каждый ингредиент должен содержать поле id.')
            if amount is None:
                raise serializers.ValidationError('Каждый ингредиент должен содержать поле amount.')
            # Проверяем количество
            if amount < 1:
                raise serializers.ValidationError(
                    f'Количество ингредиента (id={ingredient_id}) должно быть не меньше 1.'
                )
            # Проверяем дубликаты
            if ingredient_id.name in seen_ids:
                raise serializers.ValidationError(
                    f'Ингредиенты не должны повторяться (повтор id={ingredient_id}).'
                )
            seen_ids.add(ingredient_id.name)
        return value

    def create(self, validated_data):
        ingredients_data = validated_data.pop('ingredients')
        recipe = Recipe.objects.create(
            author=self.context['request'].user,
            **validated_data
        )
        self._save_ingredients(recipe, ingredients_data)
        return recipe

    def update(self, instance, validated_data):
        if 'ingredients' not in self.initial_data:
            raise serializers.ValidationError({
                'ingredients': 'Поле ingredients обязательно для обновления.'
            })
        ingredients_data = validated_data.pop('ingredients', None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        if ingredients_data is not None:
            # очистим старые
            instance.ingredient_links.all().delete()
            self._save_ingredients(instance, ingredients_data)

        return instance

    def _save_ingredients(self, recipe, ingredients_data):
        links = []
        for ing in ingredients_data:
            links.append(RecipeIngredient(
                recipe=recipe,
                ingredient=ing['ingredient'],
                amount=ing['amount']
            ))
        RecipeIngredient.objects.bulk_create(links)


class FavoriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Favorite
        fields = ('user', 'recipe')


class ShoppingCartSerializer(serializers.ModelSerializer):
    class Meta:
        model = ShoppingCart
        fields = ('user', 'recipe')


class SubscriptionSerializer(serializers.ModelSerializer):
    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.SerializerMethodField()

    class Meta:
        model = Subscription
        fields = (
            'id', 'email', 'username', 'first_name', 'last_name', 'avatar', 'is_subscribed', 'recipes', 'recipes_count')

    id = serializers.ReadOnlyField(source='author.id')
    email = serializers.ReadOnlyField(source='author.email')
    username = serializers.ReadOnlyField(source='author.username')
    first_name = serializers.ReadOnlyField(source='author.first_name')
    last_name = serializers.ReadOnlyField(source='author.last_name')
    avatar = serializers.ReadOnlyField(source='author.avatar_url')
    is_subscribed = serializers.SerializerMethodField()

    def get_is_subscribed(self, obj):
        return True

    def get_recipes(self, obj):
        limit = self.context['request'].query_params.get('recipes_limit')
        qs = Recipe.objects.filter(author=obj.author)
        if limit and limit.isdigit():
            qs = qs[:int(limit)]
        return RecipeMinifiedSerializer(qs, many=True).data

    def get_recipes_count(self, obj):
        return Recipe.objects.filter(author=obj.author).count()


class ShortLinkSerializer(serializers.ModelSerializer):
    class Meta:
        model = ShortLink
        fields = []

    def to_representation(self, instance):
        request = self.context.get('request')
        rel = instance.get_short_url()
        full = request.build_absolute_uri(rel)
        return {'short-link': full}


class SetAvatarSerializer(serializers.ModelSerializer):
    avatar = Base64ImageField()

    class Meta:
        model = User
        fields = ('avatar',)


class SetPasswordSerializer(serializers.Serializer):
    current_password = serializers.CharField(write_only=True)
    new_password = serializers.CharField(write_only=True)


class TokenCreateSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)


class TokenGetResponseSerializer(serializers.Serializer):
    auth_token = serializers.CharField()
