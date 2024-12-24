from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
import pickle
import numpy as np
from typing import Dict

app = FastAPI(
    title="Game Win Probability Prediction API",
    description="API for predicting player win probability in their next game",
    version="1.0.0"
)


class PlayerStats(BaseModel):
    player_id: str = Field(..., min_length=1, max_length=50, description="Unique identifier for the player")
    game_name: str = Field(..., min_length=1, max_length=100, description="Name of the game being played")
    avg_session_duration: float = Field(..., gt=0, description="Average session duration in minutes")
    historical_win_rate: float = Field(..., ge=0, le=1, description="Historical win rate between 0 and 1")
    avg_moves_per_game: float = Field(..., gt=0, description="Average number of moves per game")
    total_games_played: int = Field(..., gt=0, description="Total number of games played")
    age: int = Field(..., gt=0, lt=120, description="Player's age")

    class Config:
        schema_extra = {
            "example": {
                "player_id": "PLAYER123",
                "game_name": "Chess",
                "avg_session_duration": 25.5,
                "historical_win_rate": 0.6,
                "avg_moves_per_game": 45.2,
                "total_games_played": 100,
                "age": 28
            }
        }


# Load the saved model and scaler
try:
    with open('win_probability_model.pkl', 'rb') as f:
        model = pickle.load(f)
    with open('win_probability_scaler.pkl', 'rb') as f:
        scaler = pickle.load(f)
except FileNotFoundError as e:
    raise RuntimeError("Model files not found. Please ensure model files are in the correct location.")


@app.get("/")
async def root():
    return {
        "message": "Game Win Probability Prediction API",
        "status": "active",
        "endpoints": {
            "/predict": "POST - Get win probability prediction",
            "/health": "GET - Check API health"
        }
    }


@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "model_loaded": model is not None,
        "scaler_loaded": scaler is not None
    }


@app.post("/predict", response_model=Dict[str, float])
async def predict_win_probability(player_stats: PlayerStats):
    try:
        # Calculate games_experience (log transformed)
        games_experience = np.log1p(player_stats.total_games_played)

        # Create feature array
        features = np.array([[
            player_stats.avg_session_duration,
            player_stats.historical_win_rate,
            player_stats.avg_moves_per_game,
            games_experience,
            player_stats.age
        ]])

        # Scale features
        scaled_features = scaler.transform(features)

        # Get prediction probability
        win_probability = model.predict_proba(scaled_features)[0][1]

        return {
            "player_id": player_stats.player_id,
            "game_name": player_stats.game_name,
            "win_probability": float(win_probability)
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error making prediction: {str(e)}"
        )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)