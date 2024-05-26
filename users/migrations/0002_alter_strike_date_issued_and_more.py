# Generated by Django 5.0.2 on 2024-05-24 15:37

import datetime
import django.core.validators
import django.utils.timezone
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='strike',
            name='date_issued',
            field=models.DateField(default=django.utils.timezone.now, validators=[django.core.validators.MinValueValidator(datetime.date(1888, 1, 1)), django.core.validators.MaxValueValidator(datetime.date(2024, 5, 24))]),
        ),
        migrations.AlterField(
            model_name='strike',
            name='expiration_date',
            field=models.DateField(validators=[django.core.validators.MinValueValidator(datetime.date(1888, 1, 1)), django.core.validators.MaxValueValidator(datetime.date(2025, 5, 24))]),
        ),
    ]
