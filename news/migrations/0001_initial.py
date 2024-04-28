from django.db import migrations
from django.contrib.auth.models import Group
from django.db.utils import IntegrityError

def create_writer_role(apps, schema_editor):
    Group.objects.get_or_create(name='Writer')

class Migration(migrations.Migration):

    dependencies = [
        ('movies', '0015_alter_review_publicationdate')
    ]

    operations = [
        migrations.RunPython(create_writer_role),
    ]
