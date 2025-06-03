from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (
    IngredientViewSet,
    RecipeViewSet,
    UserViewSet,
)

app_name = "api"

router = DefaultRouter()
router.register(r"users", UserViewSet, basename="users")
router.register(r"recipes", RecipeViewSet, basename="recipes")
router.register(r"ingredients", IngredientViewSet, basename="ingredients")

urlpatterns = [
    path("", include(router.urls)),
    path("auth/", include("djoser.urls.authtoken")),
]
