import joblib
import numpy as np
from typing import Dict, List


class FeaturePreprocessor:
    def __init__(self, db_config: Dict):
        self.db_config = db_config
        self.scalers = {}
        self.label_encoders = {}

    def fetch_data(self) -> pd.DataFrame:
        """Fetch data from MySQL database"""
        conn = mysql.connector.connect(**self.db_config)

        query = """
        SELECT 
            pgs.*, 
            p.age, 
            p.gender,
            p.country,
            g.name as game_name,
            DATEDIFF(NOW(), pgs.last_played) as days_since_last_played
        FROM player_game_stats pgs
        JOIN players p ON pgs.player_id = p.player_id
        JOIN games g ON pgs.game_id = g.game_id
        """

        df = pd.read_sql(query, conn)
        conn.close()
        return df

    def prepare_features(self, df: pd.DataFrame) -> Tuple[Dict, Dict]:
        """Prepare feature sets for different prediction tasks"""
        # Common preprocessing
        for cat_col in ['gender', 'country', 'game_name']:
            self.label_encoders[cat_col] = LabelEncoder()
            df[f'{cat_col}_encoded'] = self.label_encoders[cat_col].fit_transform(df[cat_col])

        # Engagement features
        engagement_features = [
            'total_games_played', 'total_moves', 'total_time_played_minutes',
            'win_ratio', 'rating', 'age', 'days_since_last_played',
            'gender_encoded', 'country_encoded', 'game_name_encoded'
        ]

        # Churn features
        churn_features = engagement_features + ['highest_score']

        # Level classification features
        level_features = [
            'total_games_played', 'win_ratio', 'total_time_played_minutes',
            'rating', 'total_moves', 'highest_score', 'age',
            'gender_encoded', 'country_encoded', 'game_name_encoded'
        ]

        # Win probability features
        win_features = [
            'total_games_played', 'win_ratio', 'rating',
            'player_level', 'total_moves', 'age',
            'gender_encoded', 'country_encoded', 'game_name_encoded'
        ]

        feature_sets = {
            'engagement': engagement_features,
            'churn': churn_features,
            'level': level_features,
            'win_prob': win_features
        }

        # Scale numerical features
        for feature_set in feature_sets.values():
            numerical_features = [f for f in feature_set if df[f].dtype in ['int64', 'float64']]
            scaler = StandardScaler()
            df[numerical_features] = scaler.fit_transform(df[numerical_features])
            self.scalers[str(feature_set)] = scaler

        target_variables = {
            'engagement': 'total_games_played',
            'churn': 'churned',
            'level': 'player_level',
            'win_prob': 'win_ratio'
        }

        return feature_sets, target_variables