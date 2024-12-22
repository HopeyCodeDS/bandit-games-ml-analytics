from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
import uuid
import pandas as pd
from datetime import datetime

from . import models, schemas
from .schemas import *
from .database import SessionLocal, engine
from .ml_model import EngagementPredictor

models.Base.metadata.create_all(bind=engine)

app = FastAPI()
predictor = EngagementPredictor()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@app.post("/predict-engagement/", response_model=GameEngagementResponse)
def predict_engagement(
        engagement: GameEngagementCreate,
        db: Session = Depends(get_db)
):
    # Prepare features for prediction
    features = pd.DataFrame({
        'age': [engagement.age],
        'total_games_played': [engagement.total_games_played],
        'win_ratio': [engagement.win_ratio],
        'total_moves': [engagement.total_moves],
        'highest_score': [engagement.highest_score],
        'rating': [engagement.rating],
        'player_level': [engagement.player_level],
        'country': [engagement.country],
        'gender': [engagement.gender]
    })

    # Get prediction
    predicted_duration = predictor.predict(features)

    # Create database record
    db_engagement = models.GameEngagement(
        player_id=uuid.UUID(engagement.player_id).bytes,
        game_id=uuid.UUID(engagement.game_id).bytes,
        engagement_duration=int(predicted_duration),
        prediction_timestamp=datetime.utcnow()
    )

    db.add(db_engagement)
    db.commit()
    db.refresh(db_engagement)

    return db_engagement


@app.get("/engagements/{player_id}", response_model=List[GameEngagementResponse])
def get_player_engagements(player_id: str, db: Session = Depends(get_db)):
    player_uuid = uuid.UUID(player_id).bytes
    engagements = db.query(models.GameEngagement) \
        .filter(models.GameEngagement.player_id == player_uuid) \
        .all()

    if not engagements:
        raise HTTPException(status_code=404, detail="No engagement predictions found")

    return engagements


@app.put("/engagements/{engagement_id}/actual")
def update_actual_engagement(
        engagement_id: int,
        actual_duration: int,
        db: Session = Depends(get_db)
):
    engagement = db.query(models.GameEngagement) \
        .filter(models.GameEngagement.id == engagement_id) \
        .first()

    if not engagement:
        raise HTTPException(status_code=404, detail="Engagement record not found")

    engagement.actual_duration = actual_duration
    engagement.accuracy = abs(engagement.engagement_duration - actual_duration) / actual_duration * 100

    db.commit()
    return {"message": "Actual engagement duration updated"}