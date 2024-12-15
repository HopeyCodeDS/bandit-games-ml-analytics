from sqlalchemy import Column, Integer, String, Float, DateTime, Enum
from sqlalchemy.dialects.mysql import BINARY
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime
import enum

Base = declarative_base()


class PlayerLevel(enum.Enum):
    NOVICE = "Novice"
    INTERMEDIATE = "Intermediate"
    EXPERT = "Expert"


class Gender(enum.Enum):
    MALE = "MALE"
    FEMALE = "FEMALE"
    NON_BINARY = "NON-BINARY"
    OTHER = "OTHER"


class GameEngagement(Base):
    __tablename__ = "game_engagement"

    id = Column(Integer, primary_key=True, index=True)
    player_id = Column(BINARY(16))
    game_id = Column(BINARY(16))
    engagement_duration = Column(Integer)  # in minutes
    prediction_timestamp = Column(DateTime, default=datetime.utcnow)
    actual_duration = Column(Integer, nullable=True)
    accuracy = Column(Float, nullable=True)