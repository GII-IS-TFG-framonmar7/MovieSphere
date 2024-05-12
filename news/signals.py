from django.dispatch import receiver
from django.db.models.signals import post_delete
from .models import New
from .utils import delete_images


@receiver(post_delete, sender=New)
def appmodel_delete_images(sender, **kwargs):
    delete_images(kwargs['instance'].photo.name)