from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator
from drf_extra_fields.fields import Base64ImageField
from rest_framework import serializers
from rest_framework.validators import UniqueTogetherValidator

from recipes.contsants import MIN_ING_AMOUNT, MIN_COOKING_TIME
from recipes.models import (
    Ingredient,
    Recipe,
    RecipeIngredient,
    Favorite,
    ShoppingCart,
    Subscription,
    ShortLink,
)

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    is_subscribed = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (
            "id",
            "email",
            "username",
            "first_name",
            "last_name",
            "is_subscribed",
            "avatar",
        )

    def get_is_subscribed(self, author_user):
        request = self.context.get("request")
        if not request or request.user.is_anonymous:
            return False
        return request.user.subscription_links.filter(author=author_user).exists()


class IngredientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ingredient
        fields = ("id", "name", "measurement_unit")


class RecipeMinifiedSerializer(serializers.ModelSerializer):
    class Meta:
        model = Recipe
        fields = ("id", "name", "image", "cooking_time")


class IngredientReadSerializer(serializers.ModelSerializer):
    id = serializers.ReadOnlyField(source="ingredient.id")
    name = serializers.ReadOnlyField(source="ingredient.name")
    measurement_unit = serializers.ReadOnlyField(source="ingredient.measurement_unit")

    class Meta:
        model = RecipeIngredient
        fields = ("id", "name", "measurement_unit", "amount")


class RecipeSerializer(serializers.ModelSerializer):
    author = UserSerializer(read_only=True)
    ingredients = IngredientReadSerializer(many=True, source="ingredient_links")
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()

    class Meta:
        model = Recipe
        fields = (
            "id",
            "author",
            "ingredients",
            "is_favorited",
            "is_in_shopping_cart",
            "name",
            "image",
            "text",
            "cooking_time",
        )

    def get_is_favorited(self, recipe_instance):
        request = self.context["request"]
        if request.user.is_anonymous:
            return False
        return request.user.favorite.filter(recipe=recipe_instance).exists()

    def get_is_in_shopping_cart(self, recipe_instance):
        request = self.context["request"]
        if request.user.is_anonymous:
            return False
        return request.user.shopping_carts.filter(recipe=recipe_instance).exists()


class IngredientWriteSerializer(serializers.Serializer):
    id = serializers.PrimaryKeyRelatedField(
        queryset=Ingredient.objects.all(),
        source="ingredient",
        write_only=True,
        error_messages={
            "required": "Поле id_ингредиента обязательно.",
            "does_not_exist": "Ингредиента с таким id не существует.",
        },
    )
    amount = serializers.IntegerField(
        validators=[
            MinValueValidator(
                MIN_ING_AMOUNT,
                message=f"Количество ингредиента должно быть не меньше {MIN_ING_AMOUNT}.",
            )
        ],
        error_messages={
            "required": "Поле amount обязательно.",
            "invalid": "Количество должно быть целым числом.",
        },
    )


class RecipeCreateUpdateSerializer(serializers.ModelSerializer):
    author = serializers.HiddenField(default=serializers.CurrentUserDefault())
    ingredients = IngredientWriteSerializer(
        many=True,
        required=True,
        allow_null=False,
        error_messages={
            "required": "Поле ingredients обязательно.",
            "blank": "Список ингредиентов не может быть пустым.",
            "invalid": "Неверный формат поля ingredients.",
        },
    )
    image = Base64ImageField(
        required=True,
        error_messages={
            "required": "Нужно указать фото.",
            "invalid": "Неверный формат изображения.",
        },
    )
    name = serializers.CharField(
        max_length=Recipe._meta.get_field("name").max_length,
        required=True,
        error_messages={
            "required": "Поле name обязательно.",
            "blank": "Поле name не может быть пустым.",
            "max_length": f'Длина поля name не должна превышать {Recipe._meta.get_field("name").max_length} символов.',
        },
    )
    text = serializers.CharField(
        required=True, error_messages={"required": "Поле text обязательно."}
    )
    cooking_time = serializers.IntegerField(
        validators=[
            MinValueValidator(
                MIN_COOKING_TIME,
                message=f"Время приготовления должно быть не меньше {MIN_COOKING_TIME}.",
            )
        ],
        error_messages={
            "required": "Поле cooking_time обязательно.",
            "invalid": "Время приготовления должно быть целым числом.",
        },
    )

    class Meta:
        model = Recipe
        fields = ("author", "ingredients", "image", "name", "text", "cooking_time")
        read_only_fields = ("author",)

    def validate(self, data):
        ingredients = data.get("ingredients")
        if not ingredients:
            raise serializers.ValidationError("Нужен хотя бы один ингредиент.")
        return data

    def validate_ingredients(self, ingredients_list):
        if not ingredients_list:
            raise serializers.ValidationError("Нужен хотя бы один ингредиент.")
        seen_ids = set()
        for entry in ingredients_list:
            ingredient_obj = entry.get("ingredient")
            if ingredient_obj is None:
                raise serializers.ValidationError(
                    "Каждый ингредиент должен содержать поле id."
                )
            pk = ingredient_obj.pk
            if pk in seen_ids:
                raise serializers.ValidationError(
                    f"Ингредиенты не должны повторяться (повтор id={pk})."
                )
            seen_ids.add(pk)
        return ingredients_list

    def validate_image(self, uploaded_image):
        if uploaded_image in (None, ""):
            raise serializers.ValidationError("Поле image не может быть пустым.")
        return uploaded_image

    def to_representation(self, recipe_instance):
        return RecipeSerializer(recipe_instance, context=self.context).data

    def create(self, validated_data):
        ingredients_data = validated_data.pop("ingredients")
        created_recipe = Recipe.objects.create(**validated_data)
        self._save_ingredients(created_recipe, ingredients_data)
        return created_recipe

    def update(self, instance, validated_data):
        ingredients_data = validated_data.pop("ingredients")
        instance = super().update(instance, validated_data)
        instance.ingredient_links.all().delete()
        self._save_ingredients(instance, ingredients_data)
        return instance

    def _save_ingredients(self, recipe_obj, ingredients_data):
        link_objects = []
        for ingredient_entry in ingredients_data:
            link_objects.append(
                RecipeIngredient(
                    recipe=recipe_obj,
                    ingredient=ingredient_entry["ingredient"],
                    amount=ingredient_entry["amount"],
                )
            )
        RecipeIngredient.objects.bulk_create(link_objects)


class FavoriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Favorite
        fields = ("user", "recipe")


class ShoppingCartSerializer(serializers.ModelSerializer):
    class Meta:
        model = ShoppingCart
        fields = ("user", "recipe")


class SubscribeSerializer(serializers.ModelSerializer):
    subscriber = serializers.HiddenField(default=serializers.CurrentUserDefault())

    class Meta:
        model = Subscription
        fields = ("subscriber", "author")
        validators = [
            UniqueTogetherValidator(
                queryset=Subscription.objects.all(),
                fields=("subscriber", "author"),
                message="Вы уже подписаны на этого автора.",
            )
        ]

    def validate(self, data):
        if data["subscriber"] == data["author"]:
            raise serializers.ValidationError(
                "Вы не можете подписаться на самого себя."
            )
        return data

    def to_representation(self, instance):
        return SubscriptionSerializer(instance.author, context=self.context).data


class SubscriptionSerializer(UserSerializer):
    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.IntegerField(source="recipes.count", read_only=True)

    class Meta(UserSerializer.Meta):
        fields = UserSerializer.Meta.fields + ("recipes", "recipes_count")

    def get_recipes(self, author_user):
        request = self.context["request"]
        limit_param = request.query_params.get("recipes_limit")
        qs = author_user.recipes.all()
        if limit_param and limit_param.isdigit():
            qs = qs[: int(limit_param)]
        return RecipeMinifiedSerializer(qs, many=True).data


class ShortLinkSerializer(serializers.ModelSerializer):
    class Meta:
        model = ShortLink
        fields = []

    def to_representation(self, shortlink_obj):
        request = self.context.get("request")
        relative_url = shortlink_obj.get_short_url()
        absolute_url = request.build_absolute_uri(relative_url)
        return {"short-link": absolute_url}


class SetAvatarSerializer(serializers.ModelSerializer):
    avatar = Base64ImageField()

    class Meta:
        model = User
        fields = ("avatar",)
