import base64
import uuid

from rest_framework import serializers
from rest_framework.fields import IntegerField
from rest_framework.relations import SlugRelatedField
from django.core.files.base import ContentFile
from django.shortcuts import get_object_or_404

from users.serializers import CustomUserCreateSerializer
from recipes.models import ShoppingList, Favorites, RecipeIngredient
from recipes.models import Recipe, Tags, Ingredient


class TagSerializer(serializers.ModelSerializer):
    """Сериализатор для тегов."""
    class Meta:
        model = Tags
        fields = ('id', 'name', 'color', 'slug')


class Base64ImageField(serializers.ImageField):
    """Сериализатор для изображений."""
    def to_internal_value(self, data):
        if isinstance(data, str) and data.startswith('data:image'):
            format, imgstr = data.split(';base64,')
            ext = format.split('/')[-1]
            filename = f"{uuid.uuid4()}.{ext}"
            decoded_file = base64.b64decode(imgstr)
            data = ContentFile(decoded_file, name=filename)
        elif isinstance(data, bytes):
            data = ContentFile(data, name=f"{uuid.uuid4()}.jpg")
        return super().to_internal_value(data)


class IngredientSerializer(serializers.ModelSerializer):
    """Сериализатор для ингредиентов."""
    class Meta:
        model = Ingredient
        fields = ('id', 'name', 'measurement_unit')


class ShoppingListSerializer(serializers.ModelSerializer):
    """Сериализатор для списка покупок."""
    author = SlugRelatedField(slug_field='username', read_only=True)
    image = serializers.ImageField(required=True, write_only=True)

    class Meta:
        model = ShoppingList
        fields = ('name', 'image', 'cooking_time')


class FavoritesSerializer(serializers.ModelSerializer):
    """Сериализатор избранных рецептов."""
    image = Base64ImageField(required=False, write_only=True)

    class Meta:
        model = Favorites
        fields = ('id', 'name', 'image', 'cooking_time')


class IngredientInRecipeSerializer(serializers.ModelSerializer):
    """Сериализатор для модели ингредиентов в рецепте."""
    id = IntegerField(write_only=True)
    amount = serializers.IntegerField()

    class Meta:
        model = RecipeIngredient
        fields = ('id', 'amount')

    def to_internal_value(self, data):
        data['amount'] = int(data['amount'])
        return super().to_internal_value(data)


class RecipeSerializer(serializers.ModelSerializer):
    """Сериалищатор для просмотра рецептов."""
    ingredients = serializers.SerializerMethodField()
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()
    author = CustomUserCreateSerializer(read_only=True)
    tags = TagSerializer(many=True, read_only=True)

    class Meta:
        model = Recipe
        fields = (
            'id',
            'tags',
            'author',
            'ingredients',
            'is_favorited',
            'is_in_shopping_cart',
            'name',
            'image',
            'text',
            'cooking_time',
        )

    def get_ingredients(self, obj):
        ingredients_data = obj.ingredients.through.objects.filter(recipe=obj)
        return [{'id': item.ingredient.id,
                 'name': item.ingredient.name,
                 'measurement_unit': item.ingredient.measurement_unit,
                 'amount': item.amount} for item in ingredients_data]

    def get_is_favorited(self, obj):
        user = self.context['request'].user
        return obj.favorites_recipe.filter(user=user).exists()

    def get_is_in_shopping_cart(self, obj):
        user = self.context['request'].user
        return obj.is_in_shopping_cart.filter(user=user).exists()


class CreateUpdateRecipeSerializer(serializers.ModelSerializer):
    """Сериализатор для создания рецептов."""
    author = CustomUserCreateSerializer(read_only=True)
    image = Base64ImageField(use_url=True)
    ingredients = IngredientInRecipeSerializer(many=True)
    tags = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=Tags.objects.all()
    )

    class Meta:
        model = Recipe
        fields = (
            'id', 'author', 'name', 'image',
            'text', 'tags', 'cooking_time', 'ingredients',
        )

    def add_ingredient(self, recipe, ingredient_id, amount):
        """Метод добавления ингредиента."""
        ingredient = get_object_or_404(Ingredient, id=ingredient_id)
        try:
            recipe_ingredient = RecipeIngredient.objects.get(
                recipe=recipe,
                ingredient=ingredient
            )
            recipe_ingredient.amount += amount
            recipe_ingredient.save()
        except RecipeIngredient.DoesNotExist:
            recipe_ingredient = RecipeIngredient(
                recipe=recipe,
                ingredient=ingredient,
                amount=amount
            )
            recipe_ingredient.save()
        return recipe_ingredient

    def create_tags(self, tags, recipe):
        """Метод добавления тега"""

        recipe.tags.set(tags)

    def create(self, validated_data):
        """Создание рецепта."""
        author = self.context.get('request').user
        tags = validated_data.pop('tags')
        ingredients_data = validated_data.pop('ingredients')

        recipe = Recipe.objects.create(**validated_data)
        recipe.author = author
        recipe.save()

        self.create_tags(tags, recipe)

        for ingredient_data in ingredients_data:
            ingredient_id = ingredient_data['id']
            amount = ingredient_data['amount']
            self.add_ingredient(recipe, ingredient_id, amount)

        return recipe

    def update(self, instance, validated_data):
        """Обновление рецепта."""
        instance.tags.clear()
        instance.tags.set(validated_data.pop('tags'))
        RecipeIngredient.objects.filter(recipe=instance).delete()
        ingredients_data = validated_data.pop('ingredients')
        for ingredient_data in ingredients_data:
            ingredient_id = ingredient_data['id']
            amount = ingredient_data['amount']
            self.add_ingredient(instance, ingredient_id, amount)

        image_data = validated_data.get('image')
        if image_data:
            if instance.image:
                instance.image.delete()
            instance.image = image_data

        if 'text' in validated_data:
            instance.text = validated_data['text']

        if 'name' in validated_data:
            instance.name = validated_data['name']

        instance.save()
        return instance

    def to_representation(self, instance):
        return RecipeSerializer(instance,
                                context=self.context).data


class PublicRecipeSerializer(serializers.ModelSerializer):
    """Просмотр рецепта для неавторизованного пользователя."""
    tags = TagSerializer(many=True, read_only=True)
    author = CustomUserCreateSerializer(read_only=True)

    class Meta:
        model = Recipe
        fields = (
            'id',
            'tags',
            'author',
            'name',
            'image',
            'text',
            'cooking_time',
        )


class MiniRecipeSerializer(serializers.ModelSerializer):
    """Сериализатор для краткого представления."""
    image = Base64ImageField()

    class Meta:
        model = Recipe
        fields = (
            'id',
            'name',
            'image',
            'cooking_time'
        )
