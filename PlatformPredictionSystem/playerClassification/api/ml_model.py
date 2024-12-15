
import joblib
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import StandardScaler


class EngagementPredictor:
    def __init__(self):
        self.model = joblib.load('rf_engagement_model.pkl')
        self.scaler = joblib.load('scaler.pkl')

    def predict(self, features):
        scaled_features = self.scaler.transform(features)
        return self.model.predict(scaled_features)[0]