from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from sqlalchemy import create_engine, MetaData, Table
from sqlalchemy.orm import sessionmaker
from typing import List
import uuid
import os

# FastAPI app instance
app = FastAPI()

# Database configuration
DATABASE_URL = "mysql+mysqlconnector://root:root@localhost:3307/game_analytics"
engine = create_engine(DATABASE_URL)

# ORM session setup
Session = sessionmaker(bind=engine)
metadata = MetaData()

# Player statistics table
player_game_stats_table = Table("player_game_stats", metadata, autoload_with=engine)


# Pydantic model for API response
class PlayerStats(BaseModel):
    stat_id: str  # Changed to str to handle UUID
    player_id: str  # Changed to str to handle UUID
    player_name: str
    age: int
    gender: str
    country: str
    game_id: str  # Changed to str to handle UUID
    game_name: str
    total_games_played: int
    total_wins: int
    total_losses: int
    total_moves: int
    total_time_played_minutes: int
    win_ratio: float
    rating: float
    last_played: str


@app.get("/player-stats", response_model=List[PlayerStats])
def get_player_statistics():
    """Fetch player statistics for the frontend dashboard."""
    session = Session()
    try:
        query = player_game_stats_table.select()
        results = session.execute(query).fetchall()

        if not results:
            raise HTTPException(status_code=404, detail="No player statistics found.")

        # Convert results to the expected format
        stats = []
        for row in results:
            stat = {}
            for idx, col in enumerate(player_game_stats_table.columns):
                # Handle specific type conversions
                if col.name in ["stat_id", "player_id", "game_id"]:
                    stat[col.name] = str(uuid.UUID(bytes=row[idx]))  # Convert binary to UUID string
                elif col.name == "last_played":
                    stat[col.name] = row[idx].isoformat() if row[idx] else None  # Format datetime
                else:
                    stat[col.name] = row[idx]
            stats.append(stat)

        return stats

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    finally:
        session.close()


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)