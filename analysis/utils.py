from django.conf import settings
import os

def delete_images(image_path):
    full_path = os.path.join(settings.MEDIA_ROOT, image_path)
    try:
        os.remove(full_path)
    except FileNotFoundError:
        print(f"El archivo {full_path} no existe.")
