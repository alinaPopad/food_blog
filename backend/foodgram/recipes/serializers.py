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
from django.db.models import F
from django.shortcuts import get_object_or_404



class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tags
        fields = ('id', 'name', 'color', 'slug')


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
    id = IntegerField(write_only=True)
    amount = serializers.IntegerField()

    class Meta:
        model = RecipeIngredient
        fields = ('id', 'amount')

    def to_internal_value(self, data):
        data['amount'] = int(data['amount'])
        return super().to_internal_value(data)


class RecipeSerializer(serializers.ModelSerializer):
    ingredients = serializers.SerializerMethodField()
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()

    class Meta:
        model = Recipe
        fields = '__all__'

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
    author = CustomUserCreateSerializer(read_only=True)
    image = Base64ImageField(required=False, write_only=True)
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

    def add_ingredient(self, recipe, ingredient_id, amount):
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

    def create(self, validated_data):
        author = self.context.get('request').user
        tags = validated_data.pop('tags')
        ingredients_data = validated_data.pop('ingredients')

        recipe = Recipe.objects.create(**validated_data)
        recipe.author = author
        recipe.save()
        recipe.tags.set(tags)

        for ingredient_data in ingredients_data:
            ingredient_id = ingredient_data['id']
            amount = ingredient_data['amount']
            self.add_ingredient(recipe, ingredient_id, amount)

        return recipe


#id = serializers.PrimaryKeyRelatedField(
    #    many=True,
    #    queryset=Ingredient.objects.all()
    #)

#ingredients = IngredientInRecipeSerializer(many=True, source='ingredient_used') # ,read_only=True




"""
    def create(self, validated_data):
        ingredients_data = validated_data.pop('ingredients', [])
        tags = validated_data.pop('tags')
        #author = self.context['request'].user 

        recipe = Recipe.objects.create(**validated_data)
        recipe.tags.set(tags)

        for ingredient_data in ingredients_data:
            ingredient = Ingredient.objects.get(id=ingredient_data['id'])
            amount = ingredient_data['amount']
            RecipeIngredient.objects.create(recipe=recipe,
                                            ingredient=ingredient,
                                            amount=amount)

        return recipe


        
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
 
 
"""
    class IngredientInRecipeSerializer(serializers.ModelSerializer):
   Сериализатор для модели ингредиентов в рецепте.
    name = serializers.ReadOnlyField(source='ingredient.name')
    measurement_unit = serializers.ReadOnlyField(source='ingredient.measurement_unit')

    class Meta:
        Мета-параметры сериализатора.

        model = RecipeIngredient
        fields = ('name', 'measurement_unit', 'amount', 'id')
        
        
        
        
        
        
        
        def create(self, validated_data):
        # Извлекаем данные для вложенных сериализаторов
        ingredients_data = validated_data.pop('ingredients')
        tags_data = validated_data.pop('tags')
        # Создаем рецепт
        recipe = Recipe.objects.create(**validated_data)
        
        for ingredient_data in ingredients_data:
            ingredient = Ingredient.objects.get(id=ingredient_data['id'])
            amount = ingredient_data['amount']
            RecipeIngredient.objects.create(
                recipe=recipe,
                ingredient=ingredient,
                amount=amount)

        recipe.tags.set(tags_data)
        return recipe
    
        """



"""
class RecipeSerializer(serializers.ModelSerializer):
    Сериализатор для рецептов.
    ingredients = IngredientSerializer(many=True)
    tags = TagSerializer(many=True, read_only=True)
    author = CustomUserCreateSerializer(read_only=True)
    ingredients = SerializerMethodField()
    image = Base64ImageField()
    is_favorited = SerializerMethodField(read_only=True)
    is_in_shopping_cart = SerializerMethodField(read_only=True)

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
        ingredients = getattr(obj, 'recipe_ingredients', None)
        if ingredients is not None:
            return [
                {
                    'id': ingredient.ingredient.id,
                    'name': ingredient.ingredient.name,
                    'measurement_unit': ingredient.ingredient.measurement_unit,
                    'amount': ingredient.amount
                }
                for ingredient in ingredients
            ]
        return []

    def get_is_favorited(self, obj):
        user = self.context.get('request').user
        if user.is_anonymous:
            return False
        return user.favorites.filter(recipe=obj).exists()

    def get_is_in_shopping_cart(self, obj):
        user = self.context.get('request').user
        if user.is_anonymous:
            return False
        return user.shopping_cart.filter(recipe=obj).exists()
"""


"""
    def create(self, validated_data):
       Добавление записей в связных таблицах
        request = self.context.get('request')
        ingredients = validated_data.pop('ingredients')
        tags = validated_data.pop('tags')
        recipe = Recipe.objects.create(author=request.user, **validated_data)
        recipe.tags.set(tags)
        self.create_ingredient(ingredients, recipe)
        return recipe
    
    def to_representation(self, instance):
        return RecipeSerializer(instance, context={
            'request': self.context.get('request')
        }).data



        #def create_ingredient(self, ingredients, recipe):
     #   for ingredient in ingredients:
      #      RecipeIngredient.objects.create(
       #         recipe=recipe,
        #        ingredient_id=ingredient.get('id'),
         #       amount=ingredient.get('amount'), )
"""