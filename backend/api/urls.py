from django.urls import include, path
from rest_framework.routers import DefaultRouter
from .views import (
    IngredientViewSet, TagViewSet, RecipeViewSet, CustomUserViewSet
)

router = DefaultRouter()
router.register('users', CustomUserViewSet, basename='users')
router.register('tags', TagViewSet)
router.register('ingredients', IngredientViewSet)
router.register('recipes', RecipeViewSet)

urlpatterns = [
    path('users/me/avatar/',
         CustomUserViewSet.as_view({'put': 'avatar', 'delete': 'avatar'})),

    path('', include(router.urls)),
    path('auth/', include('djoser.urls.authtoken')),
]
