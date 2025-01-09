from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
import pandas as pd
import numpy as np
import pickle
from datetime import datetime
from typing import Dict, Optional
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="Player Analytics API",
              description="Unified API for comprehensive player predictions and analytics")

# CORS configuration
origins = [
    "http://localhost",
    "http://localhost:8080",
    "http://localhost:3000",
    "http://localhost:5173",
    "https://localhost:5173",
    "https://mango-sky-053dae803.4.azurestaticapps.net",
    "https://mango-sky-053dae803.4.azurestaticapps.net/"
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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


class PlayerPredictionRequest(BaseModel):
    """Unified request model for all player predictions"""
    total_games_played: int = Field(..., gt=0, description="Total number of games played")
    total_moves: int = Field(..., gt=0, description="Total number of moves made")
    total_wins: int = Field(..., ge=0, description="Total number of wins")
    total_losses: int = Field(..., ge=0, description="Total number of losses")
    total_time_played_minutes: int = Field(..., gt=0, description="Total time played in minutes")
    gender: str = Field(..., description="Gender of the player")
    country: str = Field(..., description="Country of the player")
    game_name: str = Field(..., description="Name of the game")
    age: int = Field(..., ge=0, description="Player's age")


class UnifiedPredictionResponse(BaseModel):
    predictions: Dict
    metadata: Dict


# Feature sets for each model
CHURN_FEATURES = ['total_games_played', 'win_ratio', 'total_time_played_minutes',
                  'total_moves', 'gender', 'country', 'game_name', 'age']

WIN_PROB_FEATURES = ['total_games_played', 'total_moves', 'total_wins', 'total_losses',
                     'gender', 'country', 'game_name', 'age']

ENGAGEMENT_FEATURES = ['game_name', 'total_games_played', 'win_ratio',
                       'gender', 'country', 'age']

CLASSIFICATION_FEATURES = ['total_games_played', 'total_moves', 'total_wins', 'total_losses',
                           'total_time_played_minutes', 'gender', 'country', 'game_name', 'age']



def prepare_features(data: pd.DataFrame, required_features: list) -> pd.DataFrame:
    """Extract only the required features from the input data"""
    return data[required_features].copy()


# Function to safely transform values
def safe_transform(encoder, series):
    transformed = series.copy()
    unknown_value = len(encoder.classes_) - 1

    for idx, value in enumerate(series):
        try:
            transformed.iloc[idx] = encoder.transform([value])[0]
        except:
            transformed.iloc[idx] = unknown_value

    return transformed

def get_churn_prediction(data: pd.DataFrame) -> dict:
    """Get churn prediction using only required features"""
    # Calculate win ratio if needed
    if 'win_ratio' not in data.columns:
        data['win_ratio'] = (data['total_wins'] / data['total_games_played']) * 100

    churn_data = prepare_features(data, CHURN_FEATURES)

    # Encode categorical variables
    churn_data['gender_encoded'] = safe_transform(churn_encoder['gender_encoder'], churn_data['gender'])
    churn_data['country_encoded'] = safe_transform(churn_encoder['country_encoder'], churn_data['country'])
    churn_data['game_encoded'] = safe_transform(churn_encoder['game_encoder'], churn_data['game_name'])

    # Prepare final features for scaling
    final_features = ['total_games_played', 'win_ratio', 'total_time_played_minutes', 'total_moves',
                      'gender_encoded', 'country_encoded', 'game_encoded', 'age']
    X = churn_data[final_features]
    X_scaled = churn_scaler.transform(X)

    prediction = churn_model.predict(X_scaled)[0]
    probability = churn_model.predict_proba(X_scaled)[0][1]

    return {
        "result": "Yes" if prediction else "No",
        "probability": f"{float(probability)}",
        "advice": get_churn_advice(probability, data['win_ratio'].iloc[0], data['total_games_played'].iloc[0])
    }


def get_win_probability(data: pd.DataFrame) -> dict:
    """Get win probability using only required features"""
    win_data = prepare_features(data, WIN_PROB_FEATURES)

    # Add player level (could be derived from other features in a more sophisticated implementation)
    win_data['player_level'] = 'intermediate'

    # Encode categorical variables
    win_data['gender_encoded'] = safe_transform(win_encoder['gender_encoder'], win_data['gender'])
    win_data['country_encoded'] = safe_transform(win_encoder['country_encoder'],win_data['country'])
    win_data['game_encoded'] = safe_transform(win_encoder['game_encoder'], win_data['game_name'])
    win_data['player_level_encoded'] = win_encoder['level_encoder'].transform(win_data['player_level'])

    # Prepare final features for scaling
    final_features = ['total_games_played', 'total_moves', 'total_wins', 'total_losses',
                      'player_level_encoded', 'gender_encoded', 'country_encoded', 'age', 'game_encoded']
    X = win_data[final_features]
    X_scaled = win_scaler.transform(X)

    prediction = float(np.clip(win_model.predict(X_scaled)[0], 0, 1))

    prediction_percentage = round(prediction * 100, 1)  # Convert to percentage and round to 1 decimal

    return {
        "probability": f"{prediction} ----> {prediction_percentage}%",
        "advice": get_win_probability_advice(prediction, win_data['player_level'].iloc[0])
    }


def get_engagement_prediction(data: pd.DataFrame) -> dict:
    """Get engagement prediction using only required features"""
    # Calculate win ratio if needed
    if 'win_ratio' not in data.columns:
        data['win_ratio'] = (data['total_wins'] / data['total_games_played']) * 100

    engagement_data = prepare_features(data, ENGAGEMENT_FEATURES)

    # Encode categorical variables
    engagement_data['gender_encoded'] = safe_transform(engagement_encoder['gender_encoder'], engagement_data['gender'])
    engagement_data['country_encoded'] = safe_transform(engagement_encoder['country_encoder'], engagement_data['country'])
    engagement_data['game_encoded'] = safe_transform(engagement_encoder['game_encoder'], engagement_data['game_name'])

    # Prepare final features for scaling
    final_features = ['total_games_played', 'win_ratio', 'gender_encoded', 'country_encoded', 'age', 'game_encoded']
    X = engagement_data[final_features]
    X_scaled = engagement_scaler.transform(X)

    prediction = float(engagement_model.predict(X_scaled)[0])
    predicted_minutes = float(engagement_model.predict(X_scaled)[0])

    # Calculate monthly stats
    monthly_hours = int(predicted_minutes // 60)
    monthly_minutes = int(predicted_minutes % 60)

    # Calculate daily average
    daily_minutes = predicted_minutes / 30  # Assuming 30 days in a month
    daily_hours = int(daily_minutes // 60)
    daily_mins = int(daily_minutes % 60)

    return {
        "predicted_engagement": {
            "monthly forecast": f"{monthly_hours} hours {monthly_minutes} minutes per month",
            "daily_average": f"{daily_hours} hours {daily_mins} minutes per day"
        },
        "raw_minutes": round(predicted_minutes, 2),
        "advice": get_engagement_advice(predicted_minutes, data['total_games_played'].iloc[0])
    }



def get_classification_prediction(data: pd.DataFrame) -> dict:
    """Get skill classification using only required features"""
    classification_data = prepare_features(data, CLASSIFICATION_FEATURES)

    # Calculate win ratio
    classification_data['win_ratio'] = (classification_data['total_wins'] /
                                        classification_data['total_games_played'] * 100)

    # Encode categorical variables
    classification_data['gender_encoded'] = safe_transform(classification_encoder['gender_encoder'], classification_data['gender'])
    classification_data['country_encoded'] = safe_transform(classification_encoder['country_encoder'], classification_data['country'])
    classification_data['game_encoded'] = safe_transform(classification_encoder['game_encoder'], classification_data['game_name'])

    # Prepare final features for scaling
    final_features = ['total_games_played', 'total_moves', 'total_wins', 'total_losses',
                      'win_ratio', 'total_time_played_minutes', 'gender_encoded',
                      'country_encoded', 'age', 'game_encoded']
    X = classification_data[final_features]
    X_scaled = classification_scaler.transform(X)

    prediction = classification_model.predict(X_scaled)[0]
    predicted_level = classification_encoder['level_encoder'].inverse_transform([prediction])[0]

    return {
        "predicted_level": str(predicted_level),
        "current_stats": {
            "games_played": int(data['total_games_played'].iloc[0]),
            "win_rate": float(round(data['win_ratio'].iloc[0], 2)),
            "total_playtime": int(data['total_time_played_minutes'].iloc[0])
        },
        "advice": get_skill_advice(predicted_level, data['win_ratio'].iloc[0])
    }



def get_churn_advice(churn_prob: float, win_rate: float, games_played: int) -> str:
    if churn_prob > 0.7:
        if win_rate < 40:
            return "This person has been facing some challenges. This person should consider trying different strategies or checking out our tutorial section for helpful tips to improve his/her gameplay."
        else:
            return "We'd love to see this person continue their gaming journey! This person needs to check out our new game modes and challenges that matches their skill level."
    elif churn_prob > 0.4:
        return "This person is showing good potential! He/She needs to keep practicing and try setting personal achievement goals to make their gaming experience more exciting."
    else:
        return "Great engagement! This person dedication to the game is impressive. This person is ready to take on some new challenges!"


def get_skill_advice(predicted_level: str, win_rate: float) -> str:
    base_message = f"Current Skill Level: {predicted_level}. "
    if win_rate > 70:
        return base_message + "Outstanding performance! This person might enjoy competing in our tournament leagues."
    elif win_rate > 50:
        return base_message + "This person is showing solid skills. He/She should try challenging him or herself with more advanced strategies."
    else:
        return base_message + "This person needs to keep practicing! He/She should focus on learning from each game to improve their strategy."


def get_engagement_advice(engagement_minutes: float, games_played: int) -> str:
    daily_avg = engagement_minutes / 30  # Assuming monthly stats
    if daily_avg > 120:
        return "This person is one of our most dedicated players! He or she needs to remember to take regular breaks for the best gaming experience."
    elif daily_avg > 60:
        return "This player has established a healthy gaming routine. He or She needs to keep up the balanced approach!"
    else:
        return "This person is maintaining a casual gaming style. He or She needs to try our quick match features to make the most of your gaming sessions!"


def get_win_probability_advice(win_prob: float, current_level: str) -> str:
    if win_prob > 0.7:
        return f"This player is showing mastery at the {current_level} level! He or She should consider taking on more challenging opponents to continue growing."
    elif win_prob > 0.5:
        return "This person have a good chance of winning his/her next game. This person needs to be consistent now on to maintain an edge!"
    else:
        return "Every game is a learning opportunity. This person should try analyzing analyzing their past games to identify areas for improvement."


@app.post("/api/predictions", response_model=UnifiedPredictionResponse)
async def get_player_predictions(request: PlayerPredictionRequest):
    try:
        # Create input DataFrame
        input_data = pd.DataFrame([request.dict()])

        # Calculate win ratio once for all models that need it
        input_data['win_ratio'] = (input_data['total_wins'] / input_data['total_games_played']) * 100

        # Make all predictions
        # Get predictions from each model using only required features
        predictions_response = {
            "churn_prediction": get_churn_prediction(input_data),
            "win_probability": get_win_probability(input_data),
            "engagement_prediction": get_engagement_prediction(input_data),
            "skill_assessment": get_classification_prediction(input_data)
        }

        return UnifiedPredictionResponse(
            predictions=predictions_response,
            metadata={
                "model_version": "v1.0",
                "timestamp": datetime.now().isoformat(),
                "analysis_type": "comprehensive"
            }
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Prediction error: {str(e)}")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8002)