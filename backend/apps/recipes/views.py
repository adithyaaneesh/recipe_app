from rest_framework.decorators import api_view, permission_classes, parser_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.response import Response
from rest_framework import status
from django.core.cache import cache
from django.db.models import Q
from .models import Recipe, Ingredient, Step, Tag, Like, Bookmark, Comment
from .serializers import RecipeSerializer, CommentSerializer


# ✅ List all recipes (with search & filter) + Create recipe
@api_view(['GET', 'POST'])
def recipe_list_view(request):

    if request.method == 'GET':
        # 🔴 Redis Cache — check if result is already cached
        cache_key = f"recipes_{request.GET.urlencode()}"  # unique key per query
        cached_data = cache.get(cache_key)

        if cached_data:
            return Response(cached_data)   # Return cached result instantly

        # Query filters
        queryset = Recipe.objects.filter(is_public=True).order_by('-created_at')

        search = request.GET.get('search')
        tag = request.GET.get('tag')
        difficulty = request.GET.get('difficulty')

        if search:
            queryset = queryset.filter(
                Q(title__icontains=search) |
                Q(description__icontains=search) |
                Q(ingredients__name__icontains=search)
            ).distinct()

        if tag:
            queryset = queryset.filter(tags__name__icontains=tag)

        if difficulty:
            queryset = queryset.filter(difficulty=difficulty)

        serializer = RecipeSerializer(queryset, many=True, context={'request': request})

        # 🔴 Save to Redis cache for 5 minutes (300 seconds)
        cache.set(cache_key, serializer.data, timeout=300)

        return Response(serializer.data)

    elif request.method == 'POST':
        if not request.user.is_authenticated:
            return Response({'error': 'Login required'}, status=status.HTTP_401_UNAUTHORIZED)

        serializer = RecipeSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            recipe = serializer.save(author=request.user)

            # Handle ingredients
            ingredients_data = request.data.get('ingredients', [])
            for ing in ingredients_data:
                Ingredient.objects.create(recipe=recipe, **ing)

            # Handle steps
            steps_data = request.data.get('steps', [])
            for step in steps_data:
                Step.objects.create(recipe=recipe, **step)

            # Handle tags
            tags_data = request.data.get('tags', [])
            for tag_name in tags_data:
                tag_obj, _ = Tag.objects.get_or_create(name=tag_name.lower())
                recipe.tags.add(tag_obj)

            # 🔴 Clear recipe list cache when new recipe is added
            cache.delete_pattern("recipes_*")

            return Response(RecipeSerializer(recipe, context={'request': request}).data,
                            status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# ✅ Get, Update, Delete a single recipe
@api_view(['GET', 'PUT', 'DELETE'])
def recipe_detail_view(request, pk):
    try:
        recipe = Recipe.objects.get(pk=pk)
    except Recipe.DoesNotExist:
        return Response({'error': 'Recipe not found'}, status=status.HTTP_404_NOT_FOUND)

    if request.method == 'GET':
        serializer = RecipeSerializer(recipe, context={'request': request})
        return Response(serializer.data)

    elif request.method == 'PUT':
        if request.user != recipe.author:
            return Response({'error': 'Not authorized'}, status=status.HTTP_403_FORBIDDEN)

        serializer = RecipeSerializer(recipe, data=request.data, partial=True,
                                      context={'request': request})
        if serializer.is_valid():
            serializer.save()
            cache.delete_pattern("recipes_*")   # Clear cache on update
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    elif request.method == 'DELETE':
        if request.user != recipe.author:
            return Response({'error': 'Not authorized'}, status=status.HTTP_403_FORBIDDEN)

        recipe.delete()
        cache.delete_pattern("recipes_*")   # Clear cache on delete
        return Response({'message': 'Recipe deleted'}, status=status.HTTP_204_NO_CONTENT)


# ✅ Like / Unlike a recipe
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def like_recipe_view(request, pk):
    try:
        recipe = Recipe.objects.get(pk=pk)
    except Recipe.DoesNotExist:
        return Response({'error': 'Recipe not found'}, status=status.HTTP_404_NOT_FOUND)

    like, created = Like.objects.get_or_create(user=request.user, recipe=recipe)

    if not created:
        like.delete()   # Already liked → unlike
        return Response({'message': 'Unliked', 'liked': False})

    return Response({'message': 'Liked', 'liked': True})


# ✅ Bookmark / Unbookmark a recipe
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def bookmark_recipe_view(request, pk):
    try:
        recipe = Recipe.objects.get(pk=pk)
    except Recipe.DoesNotExist:
        return Response({'error': 'Recipe not found'}, status=status.HTTP_404_NOT_FOUND)

    bookmark, created = Bookmark.objects.get_or_create(user=request.user, recipe=recipe)

    if not created:
        bookmark.delete()
        return Response({'message': 'Bookmark removed', 'bookmarked': False})

    return Response({'message': 'Bookmarked', 'bookmarked': True})


# ✅ Comments on a recipe
@api_view(['GET', 'POST'])
def comment_view(request, pk):
    try:
        recipe = Recipe.objects.get(pk=pk)
    except Recipe.DoesNotExist:
        return Response({'error': 'Recipe not found'}, status=status.HTTP_404_NOT_FOUND)

    if request.method == 'GET':
        comments = recipe.comments.all().order_by('-created_at')
        serializer = CommentSerializer(comments, many=True)
        return Response(serializer.data)

    elif request.method == 'POST':
        if not request.user.is_authenticated:
            return Response({'error': 'Login required'}, status=status.HTTP_401_UNAUTHORIZED)

        serializer = CommentSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(user=request.user, recipe=recipe)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# ✅ Get logged-in user's bookmarked recipes
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def my_bookmarks_view(request):
    bookmarked_recipes = Recipe.objects.filter(bookmarks__user=request.user)
    serializer = RecipeSerializer(bookmarked_recipes, many=True, context={'request': request})
    return Response(serializer.data)