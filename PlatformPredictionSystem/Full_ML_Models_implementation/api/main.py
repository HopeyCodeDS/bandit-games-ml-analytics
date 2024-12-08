from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional
from .utils.preprocessing import FeaturePreprocessor
from .ml_models.model_loader import ModelLoader


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
@app.post("/predict/churn")
async def predict_churn(stats: PlayerStats):
    try:
        features = prepare_features(stats, 'churn')
        prediction = models['churn'].predict([features])[0]
        probability = models['churn'].predict_proba([features])[0][1]
        return {
            "churn_prediction": bool(prediction),
            "churn_probability": float(probability)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/predict/level")
async def predict_level(stats: PlayerStats):
    try:
        features = prepare_features(stats, 'level')
        prediction = models['level'].predict([features])[0]
        probabilities = models['level'].predict_proba([features])[0]
        return {
            "predicted_level": prediction,
            "confidence_scores": {
                "Novice": float(probabilities[0]),
                "Intermediate": float(probabilities[1]),
                "Expert": float(probabilities[2])
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/predict/win-probability")
async def predict_win_probability(stats: PlayerStats):
    try:
        features = prepare_features(stats, 'win_prob')
        prediction = models['win_prob'].predict([features])[0]
        return {"win_probability": float(prediction)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
