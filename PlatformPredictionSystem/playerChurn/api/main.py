from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import numpy as np
import pandas as pd
import pickle
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime, timedelta

# Load model and scaler
with open('../model/churn_model.pkl', 'rb') as f:
    model = pickle.load(f)
with open('../model/churn_scaler.pkl', 'rb') as f:
    scaler = pickle.load(f)

# Define the engagement score threshold from model training
ENGAGEMENT_THRESHOLD = 180.3772307692308

# Create FastAPI app
app = FastAPI()

origins = [
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


class PlayerData(BaseModel):
    total_time_played_minutes: int
    total_games_played: int
    total_wins: int
    total_moves: int
    age: int
    last_played: datetime

    class Config:
        json_schema_extra = {
            "example": {
                "total_time_played_minutes": 500,
                "total_games_played": 50,
                "total_wins": 25,
                "total_moves": 1000,
                "age": 25,
                "last_played": "2024-03-14T12:00:00"
            }
        }


@app.get("/")
def root():
    return {"message": "Welcome to the ML Model API for Player Churn Prediction!"}


@app.post("/predict/churn")
async def predict_churn(player_data: PlayerData):
    try:
        # Calculate engineered features
        avg_session_duration = player_data.total_time_played_minutes / player_data.total_games_played
        win_rate = player_data.total_wins / player_data.total_games_played
        avg_moves_per_game = player_data.total_moves / player_data.total_games_played

        # Calculate engagement score (same weights as in training)
        engagement_score = (player_data.total_time_played_minutes * 0.4 +
                            player_data.total_games_played * 0.3 +
                            win_rate * 0.3)

        # Create feature array matching the model's expected features
        features = pd.DataFrame([{
            'avg_session_duration': avg_session_duration,
            'win_rate': win_rate,
            'avg_moves_per_game': avg_moves_per_game,
            'total_games_played': player_data.total_games_played,
            'age': player_data.age
        }])

        # Scale features
        scaled_features = scaler.transform(features)

        # Get model prediction
        churn_prob = model.predict_proba(scaled_features)[0][1]

        # Determine churn status based on engagement score threshold
        is_churned = engagement_score < ENGAGEMENT_THRESHOLD

        return {
            "churn_probability": float(churn_prob),
            "is_churned": bool(is_churned),
            "churn_status": "Churned" if is_churned else "Not Churned",
            "engagement_score": float(engagement_score),
            "engagement_threshold": float(ENGAGEMENT_THRESHOLD),
            "prediction_timestamp": datetime.now().isoformat(),
            "features_used": {
                "avg_session_duration": float(avg_session_duration),
                "win_rate": float(win_rate),
                "avg_moves_per_game": float(avg_moves_per_game),
                "total_games_played": player_data.total_games_played,
                "age": player_data.age
            }
        }

    except ZeroDivisionError:
        raise HTTPException(
            status_code=400,
            detail="Invalid data: Cannot calculate rates with zero games played"
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)