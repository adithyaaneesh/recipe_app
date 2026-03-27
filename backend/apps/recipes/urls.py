from django.urls import path
from . import views

urlpatterns = [
    path('', views.recipe_list_view, name='recipe-list'),
    path('<int:pk>/', views.recipe_detail_view, name='recipe-detail'),
    path('<int:pk>/like/', views.like_recipe_view, name='recipe-like'),
    path('<int:pk>/bookmark/', views.bookmark_recipe_view, name='recipe-bookmark'),
    path('<int:pk>/comments/', views.comment_view, name='recipe-comments'),
    path('bookmarks/my/', views.my_bookmarks_view, name='my-bookmarks'),
]