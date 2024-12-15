import joblib
from pathlib import Path


class ModelLoader:
    def __init__(self):
        self.models = {}
        self.load_models()

    def load_models(self):
        model_path = Path('./models')
        self.models = {
            'engagement': joblib.load(model_path / 'engagement_model.joblib'),
            'churn': joblib.load(model_path / 'churn_model.joblib'),
            'level': joblib.load(model_path / 'level_model.joblib'),
            'win_prob': joblib.load(model_path / 'win_prob_model.joblib')
        }

    def get_model(self, model_type: str):
        return self.models.get(model_type)