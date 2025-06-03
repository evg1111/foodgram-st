import csv

from django.core.management import BaseCommand, call_command
from django.db import transaction

from recipes.models import Ingredient


class Command(BaseCommand):
    def handle(self, *args, **options):
        try:
            call_command('flush', '--no-input', verbosity=0)

            call_command('migrate', verbosity=0)

            with transaction.atomic(), open('data/ingredients.csv', 'r', encoding='utf-8') as f:
                for row in csv.DictReader(f):
                    Ingredient.objects.create(**row)

        except Exception as e:
            print(f"ERROR: {e}")
