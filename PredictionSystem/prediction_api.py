from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
import pickle
import pandas as pd
import numpy as np
from typing import Dict, Optional
from datetime import datetime
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="Player Analytics API",
              description="API for predicting player churn, win probability, engagement, and skill classification")

origins = [
    "http://localhost.tiangolo.com",
    "http://localhost",
    "http://localhost:8080",
    "http://localhost:3000",
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Load models, scalers, and encoders
try:
    # Churn model components
    with open('models/churn_model.pkl', 'rb') as f:
        churn_model = pickle.load(f)
    with open('models/churn_scaler.pkl', 'rb') as f:
        churn_scaler = pickle.load(f)
    with open('models/churn_encoders.pkl', 'rb') as f:
        churn_encoder = pickle.load(f)

    # Win probability model
    with open('models/win_probability_model.pkl', 'rb') as f:
        win_model = pickle.load(f)
    with open('models/win_probability_scaler.pkl', 'rb') as f:
        win_scaler = pickle.load(f)
    with open('models/win_probability_encoders.pkl', 'rb') as f:
        win_encoder = pickle.load(f)

    # Engagement model
    with open('models/engagement_model.pkl', 'rb') as f:
        engagement_model = pickle.load(f)
    with open('models/engagement_scaler.pkl', 'rb') as f:
        engagement_scaler = pickle.load(f)
    with open('models/engagement_encoders.pkl', 'rb') as f:
        engagement_encoder = pickle.load(f)

    # Classification model and components
    with open('models/player_classification_model.pkl', 'rb') as f:
        classification_model = pickle.load(f)
    with open('models/player_classification_scaler.pkl', 'rb') as f:
        classification_scaler = pickle.load(f)
    with open('models/player_classification_encoders.pkl', 'rb') as f:
        classification_encoder = pickle.load(f)

except Exception as e:
    print(f"Error loading models and components: {str(e)}")
    raise RuntimeError(f"Failed to load required models and components: {str(e)}")


# Define request models
class ChurnPredictionRequest(BaseModel):
    total_games_played: int = Field(..., gt=0, description="Total number of games played")
    win_ratio: float = Field(..., ge=0, le=100, description="Win ratio as a percentage")
    total_time_played_minutes: int = Field(..., gt=0, description="Total time played in minutes")
    total_moves: int = Field(..., gt=0, description="Total number of moves made")
    gender: str = Field(..., description="Gender of the player")
    country: str = Field(..., description="Country of the player")
    game_name: str = Field(..., description="Name of the game")
    age: int = Field(..., ge=0, description="Player's age")


class WinProbabilityRequest(BaseModel):
    total_games_played: int = Field(..., gt=0)
    total_wins: int = Field(..., ge=0)
    total_losses: int = Field(..., ge=0)
    total_moves: int = Field(..., gt=0)
    player_level: str = Field(..., description="Player's skill level")
    gender: str = Field(..., description="Gender of the player")
    country: str = Field(..., description="Country of the player")
    game_name: str = Field(..., description="Name of the game")
    age: int = Field(..., ge=0)


class EngagementPredictionRequest(BaseModel):
    game_name: str = Field(..., description="Name of the game")
    total_games_played: int = Field(..., gt=0)
    win_ratio: float = Field(..., ge=0, le=100)
    gender: str = Field(..., description="Gender of the player")
    country: str = Field(..., description="Country of the player")
    age: int = Field(..., ge=0)


class ClassificationRequest(BaseModel):
    total_games_played: int = Field(..., gt=0)
    total_moves: int = Field(..., gt=0)
    total_wins: int = Field(..., ge=0)
    total_losses: int = Field(..., ge=0)
    total_time_played_minutes: int = Field(..., gt=0)
    gender: str = Field(..., description="Gender of the player")
    country: str = Field(..., description="Country of the player")
    game_name: str = Field(..., description="Name of the game")
    age: int = Field(..., ge=0)


# Response model
class PredictionResponse(BaseModel):
    prediction: Dict
    confidence: Optional[float] = None
    metadata: Dict

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

# API Endpoints
@app.post("/predict/churn", response_model=PredictionResponse)
async def predict_churn(request: ChurnPredictionRequest):
    try:
        input_data = pd.DataFrame([request.dict()])
        process_data = preprocess_churn_data(input_data)
        prediction = churn_model.predict(process_data)[0]
        probability = churn_model.predict_proba(process_data)[0][1]
        return PredictionResponse(
            prediction={"prediction": f"Churn Prediction: {'Yes' if prediction else 'No'}"},
            confidence=probability,
            metadata={"model_version": "v1.0", "timestamp": datetime.now().isoformat()}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Prediction error: {str(e)}")


@app.post("/predict/win_probability", response_model=PredictionResponse)
async def predict_win_probability(request: WinProbabilityRequest):
    try:
        input_data = pd.DataFrame([request.dict()])
        processed_data = preprocess_win_probability_data(input_data)

        prediction = win_model.predict(processed_data)[0]
        prediction = np.clip(prediction, 0, 1)

        confidence = None
        if hasattr(win_model, 'predict_proba'):
            confidence = float(win_model.predict_proba(processed_data).max(axis=1)[0])

        return PredictionResponse(
            prediction={"win_probability": float(prediction)},
            confidence=confidence,
            metadata={
                "model_version": "v1.0",
                "timestamp": datetime.now().isoformat()
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Prediction error: {str(e)}")


@app.post("/predict/engagement", response_model=PredictionResponse)
async def predict_engagement(request: EngagementPredictionRequest):
    try:
        input_data = pd.DataFrame([request.dict()])
        processed_data = preprocess_engagement_data(input_data)

        prediction = engagement_model.predict(processed_data)[0]

        confidence = None
        if hasattr(engagement_model, 'predict_proba'):
            confidence = float(engagement_model.predict_proba(processed_data).max(axis=1)[0])

        return PredictionResponse(
            prediction={"predicted_engagement_minutes": float(prediction)},
            confidence=confidence,
            metadata={
                "model_version": "v1.0",
                "timestamp": datetime.now().isoformat()
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Prediction error: {str(e)}")

@app.post("/predict/classification", response_model=PredictionResponse)
async def predict_player_level(request: ClassificationRequest):
    try:
        input_data = pd.DataFrame([request.dict()])
        processed_data = preprocess_classification_data(input_data)

        prediction = classification_model.predict(processed_data)[0]
        predicted_level = classification_encoder['level_encoder'].inverse_transform([prediction])[0]

        confidence = None
        if hasattr(classification_model, 'predict_proba'):
            confidence = float(classification_model.predict_proba(processed_data).max(axis=1)[0])

        win_rate = (input_data['total_wins'].iloc[0] / input_data['total_games_played'].iloc[0]) * 100

        return PredictionResponse(
            prediction={
                "predicted_level": str(predicted_level),
                "stats": {
                    "games_played": int(input_data['total_games_played'].iloc[0]),
                    "wins": int(input_data['total_wins'].iloc[0]),
                    "losses": int(input_data['total_losses'].iloc[0]),
                    "win_rate": float(round(win_rate, 2)),
                    "total_playtime_minutes": int(input_data['total_time_played_minutes'].iloc[0])
                }
            },
            confidence=confidence,
            metadata={
                "model_version": "v1.0",
                "timestamp": datetime.now().isoformat()
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Prediction error: {str(e)}")

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)