from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class GameEngagementBase(BaseModel):
    player_id: str
    game_id: str
    age: int
    gender: str
    country: str
    total_games_played: int
    win_ratio: float
    total_moves: int
    highest_score: int
    rating: int
    player_level: str


class GameEngagementCreate(GameEngagementBase):
    pass


class GameEngagementResponse(GameEngagementBase):
    id: int
    engagement_duration: int
    prediction_timestamp: datetime

    class Config:
        orm_mode = True