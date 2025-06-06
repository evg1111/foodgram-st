import csv

from django.core.management import BaseCommand, call_command
from django.db import transaction

from recipes.models import Ingredient


class Command(BaseCommand):
    help = "Очистка БД, применение миграций и массовая загрузка ингредиентов из CSV"

    def handle(self, *args, **options):
        try:
            call_command("flush", "--no-input", verbosity=0)

            call_command("migrate", verbosity=0)

            ingredients_to_create = []
            with open("data/ingredients.csv", "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    ingredients_to_create.append(
                        Ingredient(
                            name=row["name"], measurement_unit=row["measurement_unit"]
                        )
                    )

            with transaction.atomic():
                Ingredient.objects.bulk_create(ingredients_to_create)

            self.stdout.write(
                self.style.SUCCESS(
                    f"Успешно добавлено {len(ingredients_to_create)} ингредиентов"
                )
            )

        except Exception as e:
            self.stderr.write(self.style.ERROR(f"ERROR: {e}"))
