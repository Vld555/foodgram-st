import base64
from django.core.files.base import ContentFile
from rest_framework import serializers
from recipes.models import Ingredient, Tag, Recipe, RecipeIngredient, Favorite, ShoppingCart
from users.models import User
from django.contrib.auth import get_user_model
from djoser.serializers import UserCreateSerializer as DjoserUserCreateSerializer


class Base64ImageField(serializers.ImageField):
    """Кастомное поле для кодирования изображения в base64."""

    def to_internal_value(self, data):
        if isinstance(data, str) and data.startswith('data:image'):
            format, imgstr = data.split(';base64,')
            ext = format.split('/')[-1]
            data = ContentFile(base64.b64decode(imgstr), name='temp.' + ext)
        return super().to_internal_value(data)


class UserAvatarSerializer(serializers.ModelSerializer):
    avatar = Base64ImageField()

    class Meta:
        model = User
        fields = ('avatar',)


class CustomUserSerializer(serializers.ModelSerializer):
    is_subscribed = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ('email', 'id', 'username', 'first_name',
                  'last_name', 'is_subscribed', 'avatar')

    def get_is_subscribed(self, obj):
        # Пока ставим заглушку, так как логику подписок еще не писали
        return False


class RecipeShortSerializer(serializers.ModelSerializer):
    """Упрощенный вид рецепта (для подписок и списка покупок)."""
    image = Base64ImageField()

    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time')


class SubscriptionSerializer(CustomUserSerializer):
    """Сериализатор подписки: выводит автора и список его рецептов."""
    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ('email', 'id', 'username', 'first_name', 'last_name',
                  'is_subscribed', 'recipes', 'recipes_count')

    def get_recipes(self, obj):
        request = self.context.get('request')
        limit = request.GET.get('recipes_limit')
        recipes = obj.recipes.all()

        if limit:
            try:
                recipes = recipes[:int(limit)]
            except (ValueError, TypeError):
                pass

        # ВАЖНО: передаем context=self.context, чтобы сериализатор мог
        # построить полные URL для картинок
        serializer = RecipeShortSerializer(
            recipes,
            many=True,
            read_only=True,
            context=self.context
        )
        return serializer.data

    def get_recipes_count(self, obj):
        return obj.recipes.count()


class RecipeIngredientSerializer(serializers.ModelSerializer):
    """Сериализатор для вывода ингредиентов с количеством."""
    id = serializers.ReadOnlyField(source='ingredient.id')
    name = serializers.ReadOnlyField(source='ingredient.name')
    measurement_unit = serializers.ReadOnlyField(
        source='ingredient.measurement_unit')

    class Meta:
        model = RecipeIngredient
        fields = ('id', 'name', 'measurement_unit', 'amount')


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = '__all__'


class IngredientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ingredient
        fields = '__all__'


User = get_user_model()


class CustomUserCreateSerializer(DjoserUserCreateSerializer):
    class Meta:
        model = User
        fields = ('email', 'id', 'username',
                  'first_name', 'last_name', 'password')


class RecipeSerializer(serializers.ModelSerializer):
    tags = serializers.PrimaryKeyRelatedField(
        queryset=Tag.objects.all(),
        many=True,
        required=False
    )
    author = CustomUserSerializer(read_only=True)
    ingredients = RecipeIngredientSerializer(
        source='ingredient_list',
        many=True,
        read_only=True
    )
    image = Base64ImageField()
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()

    class Meta:
        model = Recipe
        fields = (
            'id', 'tags', 'author', 'ingredients',
            'is_favorited', 'is_in_shopping_cart',
            'name', 'image', 'text', 'cooking_time'
        )

    def get_is_favorited(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return Favorite.objects.filter(user=request.user, recipe=obj).exists()
        return False

    def get_is_in_shopping_cart(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return ShoppingCart.objects.filter(user=request.user, recipe=obj).exists()
        return False

    def validate(self, data):
        ingredients = self.initial_data.get('ingredients')
        if not ingredients:
            raise serializers.ValidationError(
                {'ingredients': 'Нужен хотя бы один ингредиент'})

        ingredient_list = []
        for item in ingredients:
            ingredient_id = item.get('id')
            if ingredient_id in ingredient_list:
                raise serializers.ValidationError(
                    {'ingredients': 'Ингредиенты не должны повторяться'})
            ingredient_list.append(ingredient_id)
            if int(item.get('amount')) < 1:
                raise serializers.ValidationError(
                    {'amount': 'Количество должно быть больше 0'})

        data['ingredients'] = ingredients
        return data

    def create_ingredients(self, ingredients, recipe):
        recipe_ingredients = [
            RecipeIngredient(
                recipe=recipe,
                ingredient_id=ingredient.get('id'),
                amount=ingredient.get('amount')
            )
            for ingredient in ingredients
        ]
        RecipeIngredient.objects.bulk_create(recipe_ingredients)

    def create(self, validated_data):
        ingredients = validated_data.pop('ingredients')
        tags = validated_data.pop('tags', [])

        recipe = Recipe.objects.create(**validated_data)
        if tags:
            recipe.tags.set(tags)

        self.create_ingredients(ingredients, recipe)
        return recipe

    def update(self, instance, validated_data):
        ingredients = validated_data.pop('ingredients')
        tags = validated_data.pop('tags', [])

        instance.tags.clear()
        if tags:
            instance.tags.set(tags)

        RecipeIngredient.objects.filter(recipe=instance).delete()
        self.create_ingredients(ingredients, instance)

        return super().update(instance, validated_data)

    def to_representation(self, instance):
        request = self.context.get('request')
        context = {'request': request}
        representation = super().to_representation(instance)
        from .serializers import TagSerializer
        representation['tags'] = TagSerializer(
            instance.tags.all(), many=True).data
        return representation
