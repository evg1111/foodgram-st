from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404

from recipes.models import Recipe


def redirect_to_recipe(_, short_code):
    """Редирект на страницу рецепта"""
    recipe = get_object_or_404(Recipe, short_code=short_code)
    return HttpResponseRedirect(f"/recipes/{recipe.pk}")