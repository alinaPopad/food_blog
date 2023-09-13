from django.shortcuts import render, get_object_or_404, redirect
from django.core.paginator import Paginator
from django.contrib.auth.decorators import login_required

from .models import Recipe, User, Follow
from .forms import RecipeForm

POST_FILTER = 6


def index(request):
    """Главная страница."""
    recipe = Recipe.objects.all()
    paginator = Paginator(recipe, POST_FILTER)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'recipe': recipe,
        'page_obj': page_obj,
    }
    return render(request, 'frontend/public/index.html', context)


def recipe_edit(request, recipe_id):
    """Редактирование рецепта(автор)."""
    recipe = get_object_or_404(Recipe, id=recipe_id)
    recipe_count = Recipe.objects.filter(author=recipe.author).count()
    postname_recipe = postname_recipe.text[:30] # ###
    author = recipe.author
    form = RecipeForm(request.POST or None)
    context = {
        'recipe': recipe,
        'recipe_count': recipe_count,
        'postname_recipe': postname_recipe,
        'form': form,
        'author': author,
    }
    return render(request, 'posts/post_detail.html', context)


@login_required
def post_create(request):
    """Создание рецепта."""
    form = RecipeForm(
        request.POST or None,
        files=request.FILES or None,
    )
    if request.method == 'POST':
        if form.is_valid():
            recipe = form.save(commit=False)
            recipe.author = request.user
            form.save()
            return redirect('posts:profile', recipe.author)  # страницы
    return render(request, 'posts/create_post.html', {'form': form})  # страницы


@login_required
def recipe_page(request, recipe_id):
    """Страница рецепта."""
    recipe = get_object_or_404(Recipe, id=recipe_id)
    form = RecipeForm(
        request.POST or None,
        files=request.FILES or None,
        instance=recipe
    )
    context = {
        'is_edit': True,
        'form': form,
    }
    if request.user != recipe.author:
        return redirect('recipes:recipe_detail', recipe_id)
    if request.method == 'POST':
        form = RecipeForm(
            request.POST or None,
            files=request.FILES or None,
            instance=recipe
        )
        if form.is_valid():
            form.save()
            return redirect('recipes:recipe_detail', recipe_id)
        return render(request, 'frontend/public/index.html', {'form': form})  # страницы
    return render(request, 'frontend/public/index.html', context)  # страницы


@login_required
def follow_index(request):
    """Функция для того, чтобы подписаться"""
    recipes = Recipe.objects.filter(author__following__user=request.user)
    paginator = Paginator(recipes, POST_FILTER)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    context = {
        'page_obj': page_obj
    }
    return render(request, 'posts/follow.html', context)


@login_required
def follow_page(request, username):
    """Страница подписок."""
    author = get_object_or_404(User, username=username)
    if request.user == author:
        return redirect('posts:index')
    Follow.objects.get_or_create(
        user=request.user,
        author=author,
    )
    return redirect('posts:profile', username=username)


@login_required
def profile_unfollow(request, username):
    """Функция для того, чтобы отписаться"""
    author = get_object_or_404(User, username=username)
    Follow.objects.filter(author=author, user=request.user).delete()
    return redirect('posts:profile', username=username)
