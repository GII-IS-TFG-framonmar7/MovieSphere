# Generated by Django 5.0.2 on 2024-06-08 22:26

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('news', '0013_alter_new_publicationdate'),
    ]

    operations = [
        migrations.AlterField(
            model_name='new',
            name='publicationDate',
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]
