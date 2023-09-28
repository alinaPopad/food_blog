from rest_framework import serializers
from rest_framework.relations import SlugRelatedField
from .models import Recipe, Tags, Ingredient, ShoppingList, Favorites, RecipeIngredient
from users.serializers import CustomUserCreateSerializer
from rest_framework.fields import IntegerField, SerializerMethodField
from django.db import transaction
from django.core.files.base import ContentFile
import base64
import uuid
import six
from six import string_types


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tags
        fields = ('id', 'name', 'color', 'slug')


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
    author = SlugRelatedField(slug_field='username', read_only=True)
    image = serializers.ImageField(required=True, write_only=True)

    class Meta:
        model = Favorites
        fields = ('name', 'image', 'cooking_time')


class IngredientInRecipeSerializer(serializers.ModelSerializer):
    """Сериализатор для модели ингредиентов в рецепте."""
    name = serializers.ReadOnlyField(source='ingredient.name')
    measurement_unit = serializers.ReadOnlyField(source='ingredient.measurement_unit')

    class Meta:
        """Мета-параметры сериализатора."""

        model = RecipeIngredient
        fields = ('name', 'measurement_unit', 'amount', 'id')


class RecipeSerializer(serializers.ModelSerializer):
    """Сериализатор для рецептов."""
    ingredients = IngredientSerializer(many=True)
    
    class Meta:
        fields = '__all__'
        model = Recipe


class Base64ImageField(serializers.ImageField):
    """
    Custom serializer field to handle base64-encoded images.
    """

    def to_internal_value(self, data):
        if isinstance(data, six.string_types) and data.startswith('data:image'):
            # Split the base64 data into format and data
            format, imgstr = data.split(';base64,')
            # Get the file extension (e.g., 'png', 'jpeg')
            ext = format.split('/')[-1]
            # Generate a random file name
            filename = f"{uuid.uuid4()}.{ext}"
            # Create a ContentFile from the base64 data
            decoded_file = base64.b64decode(imgstr)
            data = ContentFile(decoded_file, name=filename)
        return super().to_internal_value(data)


class CreateUpdateRecipeSerializer(serializers.ModelSerializer):
    author = CustomUserCreateSerializer(read_only=True)
    image = Base64ImageField(required=True, write_only=True)
    ingredients = IngredientInRecipeSerializer(many=True)
    tags = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=Tags.objects.all()
    )

    class Meta:
        model = Recipe
        fields = (
            'id', 'author', 'name', 'image',
            'text', 'tags', 'cooking_time', 'ingredients'
            )

    def create(self, validated_data):
        # Извлекаем данные для вложенных сериализаторов
        ingredients_data = validated_data.pop('ingredients')
        tags_data = validated_data.pop('tags')
        # Создаем рецепт
        recipe = Recipe.objects.create(**validated_data)
        
        # Сохраняем ингредиенты для рецепта
        for ingredient_data in ingredients_data:
            name = ingredient_data.get('name')
            amount = ingredient_data.get('amount')
            
            try:
                ingredient = Ingredient.objects.get(name=name)
            except Ingredient.DoesNotExist:
                raise serializers.ValidationError(f"Ingredient with name '{name}' does not exist.")
            
            RecipeIngredient.objects.create(recipe=recipe, ingredient=ingredient, amount=amount)
        recipe.tags.set(tags_data)
        return recipe
    


        """
        @transaction.atomic
    def create_ingredients_amounts(self, ingredients, recipe):
        for ingredient_data in ingredients:
            ingredient = Ingredient.objects.get(
                name=ingredient_data['name'],
                measurement_unit=ingredient_data['measurement_unit']
            )
        RecipeIngredient.objects.create(
            ingredient=ingredient,
            recipe=recipe,
            amount=ingredient_data['quantity']
        )

    def create(self, validated_data):
        tags_data = validated_data.pop('tags', [])
        ingredients_data = validated_data.pop('ingredients', [])
        recipe = Recipe.objects.create(**validated_data)
        recipe.tags.set(tags_data)
        self.create_ingredients_amounts(recipe=recipe, ingredients=ingredients_data)
        return recipe
        
        def update(self, instance, validated_data):
        tags_data = validated_data.pop('tags', [])
        ingredients_data = validated_data.pop('ingredients', [])

        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        instance.save()

        instance.tags.clear()
        for tags_data in tags_data:
            tags, created = Tags.objects.get_or_create(**tags_data)
            instance.tags.add(tags)

        RecipeIngredient.objects.filter(recipe=instance).delete()
        for ingredient_data in ingredients_data:
            ingredient, created = Ingredient.objects.get_or_create(**ingredient_data)
            RecipeIngredient.objects.create(recipe=instance, ingredient=ingredient)

        return instance
        """

        #author = CustomUserCreateSerializer()
    #image = serializers.ImageField(required=True, write_only=True)
    #tag = serializers.StringRelatedField(many=True)
    #ingredients = IngredientInRecipeSerializer(
    #    source='ingredient_list', many=True)