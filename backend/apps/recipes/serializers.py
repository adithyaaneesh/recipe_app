from rest_framework import serializers
from .models import Recipe, Ingredient, Step, Tag, Like, Bookmark, Comment
from django.contrib.auth import get_user_model

User = get_user_model()


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = ['id', 'name']


class IngredientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ingredient
        fields = ['id', 'name', 'quantity', 'unit']


class StepSerializer(serializers.ModelSerializer):
    class Meta:
        model = Step
        fields = ['id', 'step_number', 'instruction']


class CommentSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source='user.username', read_only=True)

    class Meta:
        model = Comment
        fields = ['id', 'username', 'body', 'created_at']


class RecipeSerializer(serializers.ModelSerializer):
    ingredients = IngredientSerializer(many=True, read_only=True)
    steps = StepSerializer(many=True, read_only=True)
    tags = TagSerializer(many=True, read_only=True)
    author_name = serializers.CharField(source='author.username', read_only=True)
    likes_count = serializers.SerializerMethodField()
    is_liked = serializers.SerializerMethodField()
    is_bookmarked = serializers.SerializerMethodField()

    class Meta:
        model = Recipe
        fields = [
            'id', 'author_name', 'title', 'description',
            'cook_time', 'servings', 'difficulty', 'image',
            'is_public', 'tags', 'ingredients', 'steps',
            'likes_count', 'is_liked', 'is_bookmarked', 'created_at'
        ]
        read_only_fields = ['id', 'author_name', 'created_at']

    def get_likes_count(self, obj):
        return obj.likes.count()

    def get_is_liked(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return Like.objects.filter(user=request.user, recipe=obj).exists()
        return False

    def get_is_bookmarked(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return Bookmark.objects.filter(user=request.user, recipe=obj).exists()
        return False