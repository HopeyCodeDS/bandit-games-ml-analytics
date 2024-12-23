from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
import numpy as np
from datetime import datetime
from fastapi.middleware.cors import CORSMiddleware
from preprocessing import *

app = FastAPI(title="Player Analytics API",
              description="Unified API for comprehensive player predictions and analytics")

# CORS configuration
origins = ["http://localhost", "http://localhost:8080", "http://localhost:3000"]
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


def get_churn_advice(churn_prob: float, win_rate: float, games_played: int) -> str:
    if churn_prob > 0.7:
        if win_rate < 40:
            return "We notice you've been facing some challenges. Consider trying different strategies or checking out our tutorial section for helpful tips to improve your gameplay."
        else:
            return "We'd love to see you continue your gaming journey! Check out our new game modes and challenges that match your skill level."
    elif churn_prob > 0.4:
        return "You're showing good potential! Keep practicing and try setting personal achievement goals to make your gaming experience more exciting."
    else:
        return "Great engagement! Your dedication to the game is impressive. Ready to take on some new challenges?"


def get_skill_advice(predicted_level: str, win_rate: float) -> str:
    base_message = f"Current Skill Level: {predicted_level}. "
    if win_rate > 70:
        return base_message + "Outstanding performance! You might enjoy competing in our tournament leagues."
    elif win_rate > 50:
        return base_message + "You're showing solid skills. Try challenging yourself with more advanced strategies."
    else:
        return base_message + "Keep practicing! Focus on learning from each game to improve your strategy."


def get_engagement_advice(engagement_minutes: float, games_played: int) -> str:
    daily_avg = engagement_minutes / 30  # Assuming monthly stats
    if daily_avg > 120:
        return "You're one of our most dedicated players! Remember to take regular breaks for the best gaming experience."
    elif daily_avg > 60:
        return "You've established a healthy gaming routine. Keep up the balanced approach!"
    else:
        return "You're maintaining a casual gaming style. Try our quick match features to make the most of your gaming sessions!"


def get_win_probability_advice(win_prob: float, current_level: str) -> str:
    if win_prob > 0.7:
        return f"You're showing mastery at the {current_level} level! Consider taking on more challenging opponents to continue growing."
    elif win_prob > 0.5:
        return "You have a good chance of winning your next game. Focus on consistency to maintain your edge!"
    else:
        return "Every game is a learning opportunity. Try analyzing your past games to identify areas for improvement."


@app.post("/api/predictions", response_model=UnifiedPredictionResponse)
async def get_player_predictions(request: PlayerPredictionRequest):
    try:
        # Create input DataFrame
        input_data = pd.DataFrame([request.dict()])

        # Calculate win ratio
        win_ratio = (input_data['total_wins'].iloc[0] / input_data['total_games_played'].iloc[0]) * 100
        input_data['win_ratio'] = win_ratio

        # Make all predictions
        # 1. Churn Prediction
        churn_processed = preprocess_churn_data(input_data.copy())
        churn_pred = churn_model.predict(churn_processed)[0]
        churn_prob = churn_model.predict_proba(churn_processed)[0][1]

        # 2. Win Probability
        input_data['player_level'] = 'intermediate'  # Default level for win probability
        win_processed = preprocess_win_probability_data(input_data.copy())
        win_prob = win_model.predict(win_processed)[0]
        win_prob = float(np.clip(win_prob, 0, 1))

        # 3. Engagement Prediction
        engagement_processed = preprocess_engagement_data(input_data.copy())
        engagement_pred = float(engagement_model.predict(engagement_processed)[0])

        # 4. Skill Classification
        class_processed = preprocess_classification_data(input_data.copy())
        class_pred = classification_model.predict(class_processed)[0]
        predicted_level = classification_encoder['level_encoder'].inverse_transform([class_pred])[0]

        # Compile comprehensive response
        predictions_response = {
            "churn_prediction": {
                "result": "Yes" if churn_pred else "No",
                "probability": float(churn_prob),
                "advice": get_churn_advice(churn_prob, win_ratio, input_data['total_games_played'].iloc[0])
            },
            "skill_assessment": {
                "predicted_level": str(predicted_level),
                "current_stats": {
                    "games_played": int(input_data['total_games_played'].iloc[0]),
                    "win_rate": float(round(win_ratio, 2)),
                    "total_playtime": int(input_data['total_time_played_minutes'].iloc[0])
                },
                "advice": get_skill_advice(predicted_level, win_ratio)
            },
            "engagement_prediction": {
                "predicted_minutes": float(round(engagement_pred, 2)),
                "advice": get_engagement_advice(engagement_pred, input_data['total_games_played'].iloc[0])
            },
            "win_probability": {
                "probability": float(round(win_prob, 3)),
                "advice": get_win_probability_advice(win_prob, predicted_level)
            }
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