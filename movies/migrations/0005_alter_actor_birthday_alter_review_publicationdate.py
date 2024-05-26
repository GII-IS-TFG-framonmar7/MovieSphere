# Generated by Django 5.0.2 on 2024-05-26 17:52

import datetime
import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('movies', '0004_alter_genre_name'),
    ]

    operations = [
        migrations.AlterField(
            model_name='actor',
            name='birthday',
            field=models.DateField(validators=[django.core.validators.MinValueValidator(datetime.date(1888, 1, 1)), django.core.validators.MaxValueValidator(datetime.date(2024, 5, 26))]),
        ),
        migrations.AlterField(
            model_name='review',
            name='publicationDate',
            field=models.DateField(blank=True, null=True, validators=[django.core.validators.MinValueValidator(datetime.date(1888, 1, 1)), django.core.validators.MaxValueValidator(datetime.date(2024, 5, 26))]),
        ),
    ]
