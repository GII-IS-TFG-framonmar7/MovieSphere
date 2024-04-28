from django.apps import AppConfig
from joblib import load
import os

class AiModelsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'ai_models'

    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    toxic_model_path = os.path.join(base_dir, 'ai_models/resources', 'toxic_classifier.joblib')
    toxic_vectorizer_path = os.path.join(base_dir, 'ai_models/resources', 'toxic_vectorizer.joblib')

    offensive_model_path = os.path.join(base_dir, 'ai_models/resources', 'offensive_classifier.joblib')
    offensive_vectorizer_path = os.path.join(base_dir, 'ai_models/resources', 'offensive_vectorizer.joblib')

    hate_model_path = os.path.join(base_dir, 'ai_models/resources', 'hate_classifier.joblib')
    hate_vectorizer_path = os.path.join(base_dir, 'ai_models/resources', 'hate_vectorizer.joblib')

    toxic_model = None
    toxic_vectorizer = None

    offensive_model = None
    offensive_vectorizer = None

    hate_model = None
    hate_vectorizer = None

    def ready(self):        
        if not self.toxic_model:
            self.toxic_model = load(self.toxic_model_path)
        if not self.toxic_vectorizer:
            self.toxic_vectorizer = load(self.toxic_vectorizer_path)

        if not self.offensive_model:
            self.offensive_model = load(self.offensive_model_path)
        if not self.offensive_vectorizer:
            self.offensive_vectorizer = load(self.offensive_vectorizer_path)

        if not self.hate_model:
            self.hate_model = load(self.hate_model_path)
        if not self.hate_vectorizer:
            self.hate_vectorizer = load(self.hate_vectorizer_path)
