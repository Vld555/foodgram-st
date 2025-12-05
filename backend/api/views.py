from django.shortcuts import render

# Create your views here.
from rest_framework import viewsets
from recipes.models import Ingredient, Tag
from .serializers import IngredientSerializer, TagSerializer

class TagViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    pagination_class = None  # Для тегов пагинация обычно не нужна, их мало


class IngredientViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    pagination_class = None  # Отключаем пагинацию для ингредиентов
    search_fields = ('^name',)  # Поиск по началу названия