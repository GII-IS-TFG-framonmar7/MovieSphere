# Generated by Django 5.0.2 on 2024-05-24 15:37

import datetime
import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('news', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='new',
            name='publicationDate',
            field=models.DateTimeField(blank=True, null=True, validators=[django.core.validators.MinValueValidator(datetime.datetime(1888, 1, 1, 0, 0)), django.core.validators.MaxValueValidator(datetime.datetime(2024, 5, 24, 17, 37, 8, 895087))]),
        ),
        migrations.AlterField(
            model_name='new',
            name='title',
            field=models.CharField(max_length=100),
        ),
    ]
