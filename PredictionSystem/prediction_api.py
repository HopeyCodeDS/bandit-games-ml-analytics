from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
import pickle
import pandas as pd
import numpy as np
from typing import Dict, Optional
from datetime import datetime

app = FastAPI(title="Player Analytics API",
              description="API for predicting player churn, win probability, engagement, and skill classification")

# Load all models, scalers, and additional components
try:
    # Churn model components
    with open('models/best_churn_model.pkl', 'rb') as f:
        churn_model = pickle.load(f)
    with open('churn_scaler.pkl', 'rb') as f:
        churn_scaler = pickle.load(f)
    with open('churn_thresholds.pkl', 'rb') as f:
        churn_thresholds = pickle.load(f)

    # Win probability model
    with open('win_model.pkl', 'rb') as f:
        win_model = pickle.load(f)
    with open('win_scaler.pkl', 'rb') as f:
        win_scaler = pickle.load(f)

    # Engagement model
    with open('engagement_model.pkl', 'rb') as f:
        engagement_model = pickle.load(f)
    with open('engagement_scaler.pkl', 'rb') as f:
        engagement_scaler = pickle.load(f)

    # Classification model and components
    with open('classification_model.pkl', 'rb') as f:
        classification_model = pickle.load(f)
    with open('classification_scaler.pkl', 'rb') as f:
        classification_scaler = pickle.load(f)
    with open('classification_label_encoder.pkl', 'rb') as f:
        classification_le = pickle.load(f)

    # Load encoders for categorical variables
    with open('gender_encoder.pkl', 'rb') as f:
        gender_encoder = pickle.load(f)
    with open('country_encoder.pkl', 'rb') as f:
        country_encoder = pickle.load(f)

except Exception as e:
    print(f"Error loading models and components: {str(e)}")
    raise RuntimeError(f"Failed to load required models and components: {str(e)}")


class ChurnPredictionRequest(BaseModel):
    total_games_played: int = Field(..., gt=0, description="Total number of games played")
    total_wins: int = Field(..., ge=0, description="Total number of wins")
    total_losses: int = Field(..., ge=0, description="Total number of losses")
    total_moves: int = Field(..., gt=0, description="Total number of moves made")
    total_time_played_minutes: int = Field(..., gt=0, description="Total time played in minutes")
    win_ratio: float = Field(..., ge=0, le=100, description="Win ratio as percentage")
    rating: int = Field(..., ge=1, le=5, description="Player rating (1-5)")
    age: int = Field(..., ge=0, description="Player age")
    gender_encoded: int = Field(..., description="Encoded gender value")
    country_encoded: int = Field(..., description="Encoded country value")
    days_since_last_play: int = Field(..., ge=0, description="Days since last played")


class WinPredictionRequest(BaseModel):
    total_games_played: int = Field(..., gt=0)
    total_wins: int = Field(..., ge=0)
    total_losses: int = Field(..., ge=0)
    total_moves: int = Field(..., gt=0)
    total_time_played_minutes: int = Field(..., gt=0)
    rating: int = Field(..., ge=1, le=5)
    age: int = Field(..., ge=0)
    gender_encoded: int
    country_encoded: int


class EngagementPredictionRequest(BaseModel):
    total_games_played: int = Field(..., gt=0)
    total_wins: int = Field(..., ge=0)
    total_losses: int = Field(..., ge=0)
    total_moves: int = Field(..., gt=0)
    win_ratio: float = Field(..., ge=0, le=100)
    rating: int = Field(..., ge=1, le=5)
    age: int = Field(..., ge=0)
    gender_encoded: int
    country_encoded: int


class ClassificationRequest(BaseModel):
    total_games_played: int = Field(..., gt=0)
    total_wins: int = Field(..., ge=0)
    total_losses: int = Field(..., ge=0)
    total_moves: int = Field(..., gt=0)
    total_time_played_minutes: int = Field(..., gt=0)
    win_ratio: float = Field(..., ge=0, le=100)
    age: int = Field(..., ge=0)
    gender_encoded: int
    country_encoded: int


class PredictionResponse(BaseModel):
    prediction: Dict
    confidence: Optional[float] = None
    metadata: Dict

@app.post("/predict/churn")
async def predict_churn(data: ChurnPredictionRequest):
    try:
        # Convert input data to DataFrame
        input_data = pd.DataFrame([data.dict()])

        # Scale the features
        scaled_data = churn_scaler.transform(input_data)

        # Make prediction
        prediction = churn_model.predict(scaled_data)[0]  # Get first element
        probability = churn_model.predict_proba(scaled_data)[0][1]

        return {
            "churn_predicted": bool(prediction),  # Convert np.bool_ to Python bool
            "churn_probability": float(probability)  # Convert np.float64 to Python float
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/predict/win")
async def predict_win(data: WinPredictionRequest):
    try:
        input_data = pd.DataFrame([data.dict()])
        scaled_data = win_scaler.transform(input_data)
        prediction = win_model.predict(scaled_data)[0]

        return {
            "win_probability": float(prediction)  # Convert np.float64 to Python float
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/predict/engagement")
async def predict_engagement(data: EngagementPredictionRequest):
    try:
        input_data = pd.DataFrame([data.dict()])
        scaled_data = engagement_scaler.transform(input_data)
        prediction = engagement_model.predict(scaled_data)[0]

        return {
            "predicted_engagement_minutes": float(prediction)  # Convert np.float64 to Python float
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/predict/classification")
async def predict_classification(data: ClassificationRequest):
    try:
        input_data = pd.DataFrame([data.dict()])
        scaled_data = classification_scaler.transform(input_data)
        prediction = classification_model.predict(scaled_data)[0]
        predicted_class = classification_le.inverse_transform([prediction])[0]

        return {
            "player_class": str(predicted_class)  # Ensure string type
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# Enhanced test data endpoints with more information
@app.get("/test-data/churn")
async def get_churn_test_data():
    return {
        "total_games_played": 100,
        "total_wins": 55,
        "total_losses": 45,
        "total_moves": 2000,
        "total_time_played_minutes": 3000,
        "win_ratio": 55.0,
        "rating": 4,
        "age": 25,
        "gender_encoded": 1,
        "country_encoded": 0,
        "days_since_last_play": 15
    }


@app.get("/test-data/win")
async def get_win_test_data():
    return {
        "total_games_played": 100,
        "total_wins": 55,
        "total_losses": 45,
        "total_moves": 2000,
        "total_time_played_minutes": 3000,
        "rating": 4,
        "age": 25,
        "gender_encoded": 1,
        "country_encoded": 0
    }


@app.get("/test-data/engagement")
async def get_engagement_test_data():
    return {
        "total_games_played": 100,
        "total_wins": 55,
        "total_losses": 45,
        "total_moves": 2000,
        "win_ratio": 55.0,
        "rating": 4,
        "age": 25,
        "gender_encoded": 1,
        "country_encoded": 0
    }


@app.get("/test-data/classification")
async def get_classification_test_data():
    return {
        "total_games_played": 100,
        "total_wins": 55,
        "total_losses": 45,
        "total_moves": 2000,
        "total_time_played_minutes": 3000,
        "win_ratio": 55.0,
        "age": 25,
        "gender_encoded": 1,
        "country_encoded": 0
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)