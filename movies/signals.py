from django.dispatch import receiver
from django.db.models.signals import post_delete
from .models import Image, Movie
from .utils import delete_images


@receiver(post_delete, sender=Image)
def appmodel_delete_images(sender, **kwargs):
    delete_images(kwargs['instance'].url.name)

@receiver(post_delete, sender=Movie)
def appmodel_delete_images(sender, **kwargs):
    delete_images(kwargs['instance'].image.name)