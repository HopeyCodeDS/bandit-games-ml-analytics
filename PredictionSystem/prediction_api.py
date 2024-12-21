from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
import pickle
import pandas as pd
import numpy as np
from typing import Dict, Optional
from datetime import datetime

app = FastAPI(title="Player Analytics API",
              description="API for predicting player churn, win probability, engagement, and skill classification")

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


class WinPredictionRequest(BaseModel):
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


# Endpoints
@app.post("/predict/churn", response_model=PredictionResponse)
async def predict_churn(request: ChurnPredictionRequest):
    try:
        input_data = pd.DataFrame([request.dict()])
        scaled_data = preprocess_input(input_data, churn_scaler, churn_encoder, churn_model.feature_names_in_)
        prediction = churn_model.predict(scaled_data)[0]
        probability = churn_model.predict_proba(scaled_data)[0][1]
        return PredictionResponse(
            prediction={"churn": bool(prediction)},
            confidence=probability,
            metadata={"model_version": "v1.0", "timestamp": datetime.now().isoformat()}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Prediction error: {str(e)}")


@app.post("/predict/win_probability", response_model=PredictionResponse)
async def predict_win_probability(request: WinPredictionRequest):
    try:
        input_data = pd.DataFrame([request.dict()])
        scaled_data = preprocess_input(input_data, win_scaler, win_encoder, win_model.feature_names_in_)
        prediction = win_model.predict(scaled_data)[0]
        probability = win_model.predict_proba(scaled_data)[0][1]
        return PredictionResponse(
            prediction={"win_probability": float(probability)},
            confidence=probability,
            metadata={"model_version": "v1.0", "timestamp": datetime.now().isoformat()}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Prediction error: {str(e)}")





if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)