# Generated by Django 5.0.2 on 2024-06-22 00:38

import datetime
import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('movies', '0016_alter_actor_height_alter_actor_name_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='actor',
            name='birthday',
            field=models.DateField(validators=[django.core.validators.MinValueValidator(datetime.date(1888, 1, 1)), django.core.validators.MaxValueValidator(datetime.date(2024, 6, 22))]),
        ),
        migrations.AlterField(
            model_name='review',
            name='publicationDate',
            field=models.DateField(blank=True, null=True, validators=[django.core.validators.MinValueValidator(datetime.date(1888, 1, 1)), django.core.validators.MaxValueValidator(datetime.date(2024, 6, 22))]),
        ),
    ]
