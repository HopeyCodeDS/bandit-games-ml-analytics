from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional
from .utils.preprocessing import FeaturePreprocessor
from .models.model_loader import ModelLoader

app = FastAPI(
    title="Game Analytics ML API",
    description="API for game analytics predictions",
    version="1.0.0"
)

# Initialize preprocessor and model loader
preprocessor = FeaturePreprocessor()
model_loader = ModelLoader()


class PlayerStats(BaseModel):
    total_games_played: int
    total_moves: int
    total_time_played_minutes: int
    win_ratio: float
    rating: int
    age: int
    days_since_last_played: int
    gender: str
    country: str
    game_name: str
    highest_score: Optional[int] = 0


@app.post("/predict/engagement")
async def predict_engagement(stats: PlayerStats):
    try:
        # Get features using preprocessor
        features = preprocessor.prepare_features(stats.dict(), 'engagement')

        # Get model and make prediction
        model = model_loader.get_model('engagement')
        prediction = model.predict([features])[0]

        return {"predicted_engagement": float(prediction)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))