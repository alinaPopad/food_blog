# Generated by Django 4.2.5 on 2023-09-15 16:13

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('recipes', '0003_shoppinglist_favorites_and_more'),
    ]

    operations = [
        migrations.RemoveConstraint(
            model_name='favorites',
            name='unique_favorite',
        ),
        migrations.RemoveConstraint(
            model_name='shoppinglist',
            name='unique_shopping_list',
        ),
        migrations.AddConstraint(
            model_name='favorites',
            constraint=models.UniqueConstraint(fields=('user', 'recipe'), name='unique_favorite'),
        ),
        migrations.AddConstraint(
            model_name='shoppinglist',
            constraint=models.UniqueConstraint(fields=('user', 'recipe'), name='unique_shopping_list'),
        ),
    ]