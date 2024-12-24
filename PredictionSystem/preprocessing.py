import pickle
import pandas as pd
from typing import Dict, Optional


# Load all models and components
try:
    # Load all models as before...
    with open('models/churn_model.pkl', 'rb') as f:
        churn_model = pickle.load(f)
    with open('models/churn_scaler.pkl', 'rb') as f:
        churn_scaler = pickle.load(f)
    with open('models/churn_encoders.pkl', 'rb') as f:
        churn_encoder = pickle.load(f)

    with open('models/win_probability_model.pkl', 'rb') as f:
        win_model = pickle.load(f)
    with open('models/win_probability_scaler.pkl', 'rb') as f:
        win_scaler = pickle.load(f)
    with open('models/win_probability_encoders.pkl', 'rb') as f:
        win_encoder = pickle.load(f)

    with open('models/engagement_model.pkl', 'rb') as f:
        engagement_model = pickle.load(f)
    with open('models/engagement_scaler.pkl', 'rb') as f:
        engagement_scaler = pickle.load(f)
    with open('models/engagement_encoders.pkl', 'rb') as f:
        engagement_encoder = pickle.load(f)

    with open('models/player_classification_model.pkl', 'rb') as f:
        classification_model = pickle.load(f)
    with open('models/player_classification_scaler.pkl', 'rb') as f:
        classification_scaler = pickle.load(f)
    with open('models/player_classification_encoders.pkl', 'rb') as f:
        classification_encoder = pickle.load(f)

except Exception as e:
    print(f"Error loading models and components: {str(e)}")
    raise RuntimeError(f"Failed to load required models and components: {str(e)}")


# Utility function for encoding and scaling
def preprocess_input(data: pd.DataFrame, scaler, encoders: Dict[str, object], columns: list) -> pd.DataFrame:
    for col, encoder in encoders.items():
        if col in data:
            data[col] = encoder.transform(data[col])
    return pd.DataFrame(scaler.transform(data), columns=columns)


# Preprocessing functions
def preprocess_churn_data(data: pd.DataFrame) -> pd.DataFrame:
    """Preprocess input data for churn prediction"""
    data_processed = data.copy()

    # Encode categorical variables
    data_processed['gender_encoded'] = churn_encoder['gender_encoder'].transform(data_processed['gender'])
    data_processed['country_encoded'] = churn_encoder['country_encoder'].transform(data_processed['country'])
    data_processed['game_encoded'] = churn_encoder['game_encoder'].transform(data_processed['game_name'])

    # Select features
    features = ['total_games_played', 'win_ratio', 'total_time_played_minutes', 'total_moves',
                'gender_encoded', 'country_encoded', 'game_encoded', 'age']
    X = data_processed[features]
    X_scaled = churn_scaler.transform(X)

    return pd.DataFrame(X_scaled, columns=features)


def preprocess_win_probability_data(data: pd.DataFrame) -> pd.DataFrame:
    """Preprocess input data for win probability prediction"""
    data_processed = data.copy()

    # Encode categorical variables
    data_processed['gender_encoded'] = win_encoder['gender_encoder'].transform(data_processed['gender'])
    data_processed['country_encoded'] = win_encoder['country_encoder'].transform(data_processed['country'])
    data_processed['game_encoded'] = win_encoder['game_encoder'].transform(data_processed['game_name'])
    data_processed['player_level_encoded'] = win_encoder['level_encoder'].transform(data_processed['player_level'])

    # Select features
    features = ['total_games_played', 'total_moves', 'total_wins', 'total_losses',
                'player_level_encoded', 'gender_encoded', 'country_encoded', 'age', 'game_encoded']
    X = data_processed[features]
    X_scaled = win_scaler.transform(X)

    return pd.DataFrame(X_scaled, columns=features)


def preprocess_engagement_data(data: pd.DataFrame) -> pd.DataFrame:
    """Preprocess input data for engagement prediction"""
    data_processed = data.copy()

    # Encode categorical variables
    data_processed['game_encoded'] = engagement_encoder['game_encoder'].transform(data_processed['game_name'])
    data_processed['gender_encoded'] = engagement_encoder['gender_encoder'].transform(data_processed['gender'])
    data_processed['country_encoded'] = engagement_encoder['country_encoder'].transform(data_processed['country'])

    # Select features
    features = ['total_games_played', 'win_ratio', 'gender_encoded', 'country_encoded', 'age', 'game_encoded']
    X = data_processed[features]
    X_scaled = engagement_scaler.transform(X)

    return pd.DataFrame(X_scaled, columns=features)


def preprocess_classification_data(data: pd.DataFrame) -> pd.DataFrame:
    """Preprocess input data for player classification"""
    data_processed = data.copy()

    # Calculate win ratio
    data_processed['win_ratio'] = (data_processed['total_wins'] /
                                   data_processed['total_games_played'] * 100)

    # Encode categorical variables
    data_processed['gender_encoded'] = classification_encoder['gender_encoder'].transform(data_processed['gender'])
    data_processed['country_encoded'] = classification_encoder['country_encoder'].transform(data_processed['country'])
    data_processed['game_encoded'] = classification_encoder['game_encoder'].transform(data_processed['game_name'])

    # Select features
    features = ['total_games_played', 'total_moves', 'total_wins', 'total_losses',
                'win_ratio', 'total_time_played_minutes', 'gender_encoded',
                'country_encoded', 'age', 'game_encoded']

    X = data_processed[features]
    X_scaled = classification_scaler.transform(X)

    return pd.DataFrame(X_scaled, columns=features)
