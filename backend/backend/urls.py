from django.contrib import admin
from django.urls import path, include
from rest_framework.routers import DefaultRouter

from api.auth import CustomObtainAuthToken
from api.views import UserViewSet, IngredientViewSet, RecipeViewSet
from django.views.generic.base import RedirectView

router = DefaultRouter()
router.register(r'users', UserViewSet, basename='user')
router.register(r'ingredients', IngredientViewSet, basename='ingredient')
router.register(r'recipes', RecipeViewSet, basename='recipe')

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include(router.urls)),
    path('api/auth/token/login/', CustomObtainAuthToken.as_view(), name='token-login'),
    path('api/auth/token/logout/', UserViewSet.as_view({'post': 'logout'}), name='token-logout'),
    path('api-auth/', include('rest_framework.urls')),
    path('s/<slug:code>/', RedirectView.as_view(url='/', permanent=False), name='short-link-redirect'),
]