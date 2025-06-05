from django.contrib.auth import get_user_model
from django.db.models import Sum, F
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django_filters.rest_framework.backends import DjangoFilterBackend
from rest_framework import viewsets, status
from rest_framework.authentication import TokenAuthentication
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from djoser.views import UserViewSet as DjoserSet

from recipes.models import (
    Ingredient,
    Recipe,
    Favorite,
    ShoppingCart,
    Subscription,
    ShortLink,
    RecipeIngredient,
)
from .filters import RecipeFilter, IngredientFilter
from .paginators import PageNumberPagination
from .permissions import IsAuthor
from .serializers import (
    UserSerializer,
    IngredientSerializer,
    RecipeSerializer,
    RecipeCreateUpdateSerializer,
    RecipeMinifiedSerializer,
    SubscriptionSerializer,
    ShortLinkSerializer,
    SetAvatarSerializer,
    SubscribeSerializer,
)

User = get_user_model()


class UserViewSet(DjoserSet):
    serializer_class = UserSerializer
    pagination_class = PageNumberPagination

    def get_permissions(self) -> list:
        if self.action == "me":
            return [IsAuthenticated()]
        return super().get_permissions()

    @action(
        detail=False,
        methods=["get"],
        url_path="me",
        permission_classes=[IsAuthenticated],
    )
    def me(self, request, *args, **kwargs):
        return super().me(request, *args, **kwargs)

    @action(
        detail=False,
        methods=["put", "delete"],
        url_path="me/avatar",
        permission_classes=[IsAuthenticated],
    )
    def avatar(self, request):
        if request.method == "PUT":
            avatar_data = request.data.get("avatar")
            if avatar_data in [None, ""]:
                return Response(
                    {"avatar": ["Это поле обязательно."]},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            serializer = SetAvatarSerializer(
                request.user, data=request.data, partial=True
            )
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data)
        request.user.avatar.delete(save=True)
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        methods=["post", "delete"],
        url_path=r"(?P<pk>\d+)/subscribe",
        serializer_class=SubscribeSerializer,
        permission_classes=[IsAuthenticated],
        detail=False,
    )
    def subscribe(self, request, pk=None):
        author = get_object_or_404(User, pk=pk)

        if request.method == "POST":
            serializer = self.get_serializer(data={"author": author.id}, context={"request": request})
            serializer.is_valid(raise_exception=True)
            subscription = serializer.save()
            response_serializer = SubscriptionSerializer(subscription.author, context={"request": request})
            return Response(response_serializer.data, status=status.HTTP_201_CREATED)

        deleted, _ = Subscription.objects.filter(subscriber=request.user, author=author).delete()
        if deleted:
            return Response(status=status.HTTP_204_NO_CONTENT)

        return Response(
            {"errors": "Не были подписаны"}, status=status.HTTP_400_BAD_REQUEST
        )

    @action(
        detail=False,
        methods=["get"],
        url_path="subscriptions",
        permission_classes=[IsAuthenticated],
    )
    def subscriptions(self, request):
        authors_qs = User.objects.filter(follower_links__subscriber=request.user).order_by("id")

        page = self.paginate_queryset(authors_qs)
        if page is not None:
            serializer = SubscriptionSerializer(page, many=True, context={"request": request})
            return self.get_paginated_response(serializer.data)

        serializer = SubscriptionSerializer(authors_qs, many=True, context={"request": request})
        return Response(serializer.data)


class IngredientViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    filter_backends = (DjangoFilterBackend,)
    filterset_class = IngredientFilter
    pagination_class = None
    permission_classes = (AllowAny,)


class RecipeViewSet(viewsets.ModelViewSet):
    queryset = Recipe.objects.all()
    authentication_classes = (TokenAuthentication,)
    filter_backends = (DjangoFilterBackend,)
    filterset_class = RecipeFilter
    pagination_class = PageNumberPagination

    def get_permissions(self):
        if self.action in ["list", "retrieve", "download_shopping_cart", "get_link"]:
            return [AllowAny()]
        if self.action in ["favorite", "shopping_cart"]:
            return [IsAuthenticated()]
        if self.action == "create":
            return [IsAuthenticated()]
        return [IsAuthenticated(), IsAuthor()]

    def get_serializer_class(self):
        if self.action in ["create", "update", "partial_update"]:
            return RecipeCreateUpdateSerializer
        return RecipeSerializer

    @action(detail=False, methods=["get"], url_path="download_shopping_cart")
    def download_shopping_cart(self, request):
        user = request.user
        if not user.is_authenticated:
            return Response(status=status.HTTP_401_UNAUTHORIZED)
        ingredients = (
            RecipeIngredient.objects.filter(recipe__shoppingcart__user=user)
            .values(name=F("ingredient__name"), unit=F("ingredient__measurement_unit"))
            .annotate(total=Sum("amount"))
        )
        content_lines = [
            f"{item['name']} - {item['total']} {item['unit']}" for item in ingredients
        ]
        content = "\n".join(content_lines)
        response = HttpResponse(content, content_type="text/plain")
        response["Content-Disposition"] = 'attachment; filename="shopping_cart.txt"'
        return response

    @action(detail=True, methods=["get"], url_path="get-link")
    def get_link(self, request, pk=None):
        recipe = get_object_or_404(Recipe, pk=pk)
        short, created = ShortLink.objects.get_or_create(recipe=recipe)
        serializer = ShortLinkSerializer(short, context={"request": request})
        return Response(serializer.data)

    @action(detail=True, methods=["post", "delete"], url_path="favorite")
    def favorite(self, request, pk=None):
        recipe = get_object_or_404(Recipe, pk=pk)
        if request.method == "POST":
            fav, created = Favorite.objects.get_or_create(
                user=request.user, recipe=recipe
            )
            if not created:
                return Response(
                    {"errors": "Уже в избранном"}, status=status.HTTP_400_BAD_REQUEST
                )
            serializer = RecipeMinifiedSerializer(recipe)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        else:
            deleted, _ = Favorite.objects.filter(
                user=request.user, recipe=recipe
            ).delete()
            if deleted:
                return Response(status=status.HTTP_204_NO_CONTENT)
            return Response(
                {"errors": "Не было в избранном"}, status=status.HTTP_400_BAD_REQUEST
            )

    @action(detail=True, methods=["post", "delete"], url_path="shopping_cart")
    def shopping_cart(self, request, pk=None):
        recipe = get_object_or_404(Recipe, pk=pk)
        if request.method == "POST":
            sc, created = ShoppingCart.objects.get_or_create(
                user=request.user, recipe=recipe
            )
            if not created:
                return Response(
                    {"errors": "Уже в корзине"}, status=status.HTTP_400_BAD_REQUEST
                )
            serializer = RecipeMinifiedSerializer(recipe)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        else:
            deleted, _ = ShoppingCart.objects.filter(
                user=request.user, recipe=recipe
            ).delete()
            if deleted:
                return Response(status=status.HTTP_204_NO_CONTENT)
            return Response(
                {"errors": "Не было в корзине"}, status=status.HTTP_400_BAD_REQUEST
            )
