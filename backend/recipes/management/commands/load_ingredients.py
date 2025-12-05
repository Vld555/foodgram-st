import json
import os
from django.conf import settings
from django.core.management.base import BaseCommand
from recipes.models import Ingredient

class Command(BaseCommand):
    help = 'Загрузка ингредиентов из JSON (безопасный режим)'

    def handle(self, *args, **options):
        file_path = os.path.join(settings.BASE_DIR, '..', 'data', 'ingredients.json')
        print(f"Загрузка из файла: {file_path}")

        if not os.path.exists(file_path):
            self.stdout.write(self.style.ERROR('Файл JSON не найден! Проверьте путь.'))
            return

        try:
            with open(file_path, encoding='utf-8') as f:
                data = json.load(f)
                
                # Используем счетчик для красоты
                count = 0
                for item in data:
                    # get_or_create защищает от дубликатов и не вызывает ошибку bulk_create
                    Ingredient.objects.get_or_create(
                        name=item['name'],
                        measurement_unit=item['measurement_unit']
                    )
                    count += 1

            self.stdout.write(self.style.SUCCESS(f'Успешно загружено {count} ингредиентов'))
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Ошибка: {e}'))