import requests
import os
import zipfile
from django.core.management.base import BaseCommand
from bs4 import BeautifulSoup

class Command(BaseCommand):
    help = 'Download and extract weights from Google Drive'

    def handle(self, *args, **kwargs):
        def get_confirm_token(response):
            for key, value in response.cookies.items():
                if key.startswith('download_warning'):
                    return value
            return None

        def get_download_url(response):
            soup = BeautifulSoup(response.text, 'html.parser')
            form = soup.find('form', id='download-form')
            if form:
                return form['action'], {input_tag['name']: input_tag['value'] for input_tag in form.find_all('input') if 'name' in input_tag.attrs}
            return None, None

        def download_file_from_google_drive(id, destination):
            URL = "https://docs.google.com/uc?export=download"
            session = requests.Session()

            response = session.get(URL, params={'id': id}, stream=True)
            token = get_confirm_token(response)

            if token:
                params = {'id': id, 'confirm': token}
                response = session.get(URL, params=params, stream=True)
            else:
                download_url, payload = get_download_url(response)
                if download_url and payload:
                    response = session.get(download_url, params=payload, stream=True)

            save_response_content(response, destination)

        def save_response_content(response, destination):
            CHUNK_SIZE = 32768

            os.makedirs(os.path.dirname(destination), exist_ok=True)
            with open(destination, "wb") as f:
                for chunk in response.iter_content(CHUNK_SIZE):
                    if chunk:
                        f.write(chunk)

        def unzip_file(source, destination):
            with zipfile.ZipFile(source, 'r') as zip_ref:
                zip_ref.extractall(destination)

        def rename_model_file(source, destination):
            os.rename(source, destination)

        file_id = '13gFDLFhhBqwMw6gf8jVUvNDH2UrgCCrX'
        download_destination = 'ai_models/resources/yolo/weights.zip'
        extract_destination = 'ai_models/resources/yolo/'
        final_model_path = os.path.join(extract_destination, 'yolov3-face.weights')

        download_file_from_google_drive(file_id, download_destination)
        unzip_file(download_destination, extract_destination)
        os.remove(download_destination)  # Opcional: elimina el archivo ZIP después de descomprimirlo

        # Renombra el archivo del modelo descargado
        original_model_path = os.path.join(extract_destination, 'yolov3-wider_16000.weights')
        rename_model_file(original_model_path, final_model_path)

        self.stdout.write(self.style.SUCCESS('Successfully downloaded and extracted weights'))

# Asegúrate de que los directorios en la ruta ai_models/resources/yolo/ existan antes de ejecutar el script.

if __name__ == "__main__":
    Command().handle()
