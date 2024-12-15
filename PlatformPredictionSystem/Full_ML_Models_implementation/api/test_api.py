from fastapi.testclient import TestClient
from .main import app
import pytest

client = TestClient(app)

def test_root():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Game Analytics ML API"}

def test_engagement_prediction():
    test_data = {
        "total_games_played": 50,
        "total_moves": 1000,
        "total_time_played_minutes": 500,
        "win_ratio": 0.6,
        "rating": 4,
        "age": 25,
        "days_since_last_played": 2,
        "gender": "MALE",
        "country": "USA",
        "game_name": "Chess",
        "highest_score": 100
    }
    response = client.post("/predict/engagement", json=test_data)
    assert response.status_code == 200
    assert "predicted_engagement" in response.json()