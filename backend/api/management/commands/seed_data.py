import random
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model

from faker import Faker

from api.models import Ingredient, Recipe, RecipeIngredient, Favorite, ShoppingCart, Subscription, ShortLink

User = get_user_model()


class Command(BaseCommand):
    help = 'Создаёт суперпользователя и заполняет базу тестовыми данными через Faker'

    def handle(self, *args, **options):
        fake = Faker('ru_RU')

        # Создать суперпользователя
        if not User.objects.filter(username='admin').exists():
            User.objects.create_superuser(
                username='admin',
                email='admin@example.com',
                password='admin123'
            )
            self.stdout.write(self.style.SUCCESS('Создан суперпользователь admin'))
        else:
            self.stdout.write('Суперпользователь admin уже существует')

        # Создать обычных пользователей
        users = []
        for _ in range(10):
            username = fake.user_name()
            email = fake.email()
            user = User.objects.create_user(
                username=username,
                email=email,
                password='password'
            )
            users.append(user)
        self.stdout.write(self.style.SUCCESS('Создано 10 тестовых пользователей'))

        # Создать ингредиенты
        ingredients = []
        for _ in range(20):
            name = fake.word()
            unit = random.choice(['г', 'кг', 'мл', 'шт'])
            ing = Ingredient.objects.create(name=name, measurement_unit=unit)
            ingredients.append(ing)
        self.stdout.write(self.style.SUCCESS('Создано 20 ингредиентов'))

        # Создать рецепты
        recipes = []
        for user in users:
            for _ in range(2):
                recipe = Recipe.objects.create(
                    author=user,
                    name=fake.sentence(nb_words=3),
                    text=fake.paragraph(nb_sentences=5),
                    cooking_time=random.randint(5, 120),
                )
                # Ингредиенты в рецепте
                for ing in random.sample(ingredients, k=5):
                    RecipeIngredient.objects.create(
                        recipe=recipe,
                        ingredient=ing,
                        amount=random.randint(1, 500)
                    )
                recipes.append(recipe)
        self.stdout.write(self.style.SUCCESS('Создано {} рецептов'.format(len(recipes))))

        # Добавить фавориты и в корзину
        for user in users:
            favs = random.sample(recipes, k=3)
            for rec in favs:
                Favorite.objects.get_or_create(user=user, recipe=rec)
            carts = random.sample(recipes, k=2)
            for rec in carts:
                ShoppingCart.objects.get_or_create(user=user, recipe=rec)
        self.stdout.write(self.style.SUCCESS('Добавлены избранные и корзины'))

        # Подписки
        for follower in random.sample(users, k=5):
            authors = random.sample([u for u in users if u != follower], k=3)
            for author in authors:
                Subscription.objects.get_or_create(subscriber=follower, author=author)
        self.stdout.write(self.style.SUCCESS('Создано подписок'))

        # Короткие ссылки
        for rec in recipes:
            code = fake.lexify(text='??????')
            ShortLink.objects.get_or_create(recipe=rec, defaults={'code': code})
        self.stdout.write(self.style.SUCCESS('Созданы короткие ссылки для рецептов'))

        self.stdout.write(self.style.SUCCESS('Сеанс заполнения данных завершён.'))
