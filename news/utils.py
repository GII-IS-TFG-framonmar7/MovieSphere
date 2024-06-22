from django.conf import settings
import os

def delete_images(image_path):
    full_path = os.path.join(settings.MEDIA_ROOT, image_path)
    if os.path.exists(full_path):
        os.remove(full_path)
