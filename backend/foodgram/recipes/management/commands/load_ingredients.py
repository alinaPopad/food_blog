import csv
import json
from django.core.management.base import BaseCommand
from recipes.models import Ingredient


class Command(BaseCommand):
    help = 'Load ingredients data from CSV and JSON files'

    def handle(self, *args, **kwargs):
        # Load data from CSV
        with open('data/ingredients.csv', 'r', encoding='utf-8') as csvfile:
            csv_data = csv.reader(csvfile)
            next(csv_data)
            for row in csv_data:
                title, unit = row
                Ingredient.objects.create(title=title, unit=unit)

        # Load data from JSON
        with open('data/ingredients.json', 'r', encoding='utf-8') as jsonfile:
            json_data = json.load(jsonfile)
            for item in json_data:
                title = item['name']
                unit = item['measurement_unit']
                Ingredient.objects.create(title=title, unit=unit)

        self.stdout.write(self.style.SUCCESS('Successfully loaded ingredients'))
