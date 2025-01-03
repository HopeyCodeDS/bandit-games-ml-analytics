from fastapi import FastAPI, HTTPException, Query, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session
from pydantic import BaseModel
from pydantic.types import UUID
from typing import List, Optional
from datetime import datetime
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Database configuration
DB_USER = os.getenv('DB_USER')
DB_PASSWORD = os.getenv('DB_PASSWORD')
DB_HOST = os.getenv('DB_HOST', 'localhost')
DB_PORT = os.getenv('DB_PORT', '3307')
DB_NAME = 'game_analytics'

# Create SQLAlchemy engine
DATABASE_URL = f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}?charset=utf8mb4"
engine = create_engine(DATABASE_URL, pool_pre_ping=True)

# Initialize FastAPI app
app = FastAPI(
    title="Player Statistics API",
    description="API for retrieving player game statistics for dashboard",
    version="1.0.1"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Configure this appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Pydantic models for data validation
class PlayerStats(BaseModel):
    stat_id: UUID
    player_id: UUID
    player_name: str
    age: Optional[int]
    gender: Optional[str]
    country: Optional[str]
    game_id: UUID
    game_name: str
    total_games_played: int
    total_wins: int
    total_losses: int
    total_moves: int
    total_time_played_minutes: int
    win_ratio: float
    rating: Optional[float]
    last_played: datetime

    class Config:
        from_attributes = True


# Database dependency
def get_db():
    db = Session(engine)
    try:
        yield db
    finally:
        db.close()


# API Endpoints
@app.get("/")
async def root():
    return {
        "message": "Player Statistics API",
        "version": "1.0.1",
        "endpoints": [
            "/api/stats/players",
            "/api/stats/player/{player_id}",
            "/api/stats/game/{game_id}",
            "/api/stats/summary",
            "/api/stats/most-played-games?limit=5",
            "/api/stats/top-players/{game_id}?limit=3"
        ]
    }


@app.get("/api/stats/players", response_model=List[PlayerStats])
async def get_all_player_stats(
        skip: int = Query(0, ge=0, description="Number of records to skip for pagination"),
        limit: int = Query(20, ge=1, le=100, description="Maximum number of records to return"),
        db: Session = Depends(get_db)
):
    """
    Get paginated player statistics for all players.
    """
    try:
        query = text("""
            SELECT 
                BIN_TO_UUID(stat_id) as stat_id,
                BIN_TO_UUID(player_id) as player_id,
                player_name,
                age,
                gender,
                country,
                BIN_TO_UUID(game_id) as game_id,
                game_name,
                total_games_played,
                total_wins,
                total_losses,
                total_moves,
                total_time_played_minutes,
                win_ratio,
                rating,
                last_played
            FROM player_game_stats
            ORDER BY last_played DESC
            LIMIT :skip, :limit
        """)

        result = db.execute(query, {"skip": skip, "limit": limit})
        stats = [dict(zip(result.keys(), row)) for row in result.fetchall()]

        if not stats:
            raise HTTPException(status_code=404, detail="No player statistics found")

        return stats
    except Exception as e:
        print(f"Error: {str(e)}")
        raise HTTPException(status_code=500, detail="Error retrieving player statistics")


@app.get("/api/stats/player/{player_id}", response_model=List[PlayerStats])
async def get_player_stats(
        player_id: UUID,
        db: Session = Depends(get_db)
):
    """
    Get all game statistics for a specific player.
    """
    try:
        query = text("""
            SELECT 
                BIN_TO_UUID(stat_id) as stat_id,
                BIN_TO_UUID(player_id) as player_id,
                player_name,
                age,
                gender,
                country,
                BIN_TO_UUID(game_id) as game_id,
                game_name,
                total_games_played,
                total_wins,
                total_losses,
                total_moves,
                total_time_played_minutes,
                win_ratio,
                rating,
                last_played
            FROM player_game_stats
            WHERE player_id = UUID_TO_BIN(:player_id)
        """)

        result = db.execute(query, {"player_id": str(player_id)})
        stats = [dict(zip(result.keys(), row)) for row in result.fetchall()]

        if not stats:
            raise HTTPException(
                status_code=404,
                detail=f"No statistics found for player {player_id}"
            )

        return stats
    except Exception as e:
        print(f"Error: {str(e)}")
        raise HTTPException(status_code=500, detail="Error retrieving player statistics")


@app.get("/api/stats/game/{game_id}", response_model=List[PlayerStats])
async def get_game_stats(
        game_id: UUID,
        db: Session = Depends(get_db)
):
    """
    Get all player statistics for a specific game.
    """
    try:
        query = text("""
            SELECT 
                BIN_TO_UUID(stat_id) as stat_id,
                BIN_TO_UUID(player_id) as player_id,
                player_name,
                age,
                gender,
                country,
                BIN_TO_UUID(game_id) as game_id,
                game_name,
                total_games_played,
                total_wins,
                total_losses,
                total_moves,
                total_time_played_minutes,
                win_ratio,
                rating,
                last_played
            FROM player_game_stats
            WHERE game_id = UUID_TO_BIN(:game_id)
            ORDER BY rating DESC, win_ratio DESC
        """)

        result = db.execute(query, {"game_id": str(game_id)})
        stats = [dict(zip(result.keys(), row)) for row in result.fetchall()]

        if not stats:
            raise HTTPException(
                status_code=404,
                detail=f"No statistics found for game {game_id}"
            )

        return stats
    except Exception as e:
        print(f"Error: {str(e)}")
        raise HTTPException(status_code=500, detail="Error retrieving game statistics")

@app.get("/api/stats/most-played-games")
async def get_most_played_games(
    limit: int = Query(10, ge=1, le=50, description="Number of games to return"),
    db: Session = Depends(get_db)
):
    """
    Get the most played games ranked by total matches played across all players.
    """
    try:
        query = text("""
            SELECT 
                BIN_TO_UUID(game_id) as game_id,
                game_name,
                COUNT(DISTINCT player_id) as unique_players,
                SUM(total_games_played) as total_matches,
                AVG(rating) as average_rating,
                MAX(last_played) as last_played
            FROM player_game_stats
            GROUP BY game_id, game_name
            ORDER BY total_matches DESC
            LIMIT :limit
        """)

        result = db.execute(query, {"limit": limit})
        games = [dict(zip(result.keys(), row)) for row in result.fetchall()]

        if not games:
            raise HTTPException(status_code=404, detail="No games found")

        return games
    except Exception as e:
        print(f"Error: {str(e)}")
        raise HTTPException(status_code=500, detail="Error retrieving most played games")

@app.get("/api/stats/top-players/{game_id}")
async def get_top_players_by_game(
    game_id: UUID,
    limit: int = Query(3, ge=1, le=10, description="Number of top players to return"),
    db: Session = Depends(get_db)
):
    """
    Get the top players for a specific game, ranked by rating and win ratio.
    """
    try:
        query = text("""
            SELECT 
                BIN_TO_UUID(player_id) as player_id,
                player_name,
                country,
                total_games_played,
                total_wins,
                total_losses,
                win_ratio,
                rating,
                last_played
            FROM player_game_stats
            WHERE game_id = UUID_TO_BIN(:game_id)
            ORDER BY rating DESC, win_ratio DESC
            LIMIT :limit
        """)

        result = db.execute(query, {"game_id": str(game_id), "limit": limit})
        players = [dict(zip(result.keys(), row)) for row in result.fetchall()]

        if not players:
            raise HTTPException(
                status_code=404,
                detail=f"No players found for game {game_id}"
            )

        return players
    except Exception as e:
        print(f"Error: {str(e)}")
        raise HTTPException(status_code=500, detail="Error retrieving top players")



@app.get("/api/stats/summary")
async def get_stats_summary(db: Session = Depends(get_db)):
    """
    Get summary statistics across all games and players.
    """
    try:
        query = text("""
            SELECT 
                COUNT(DISTINCT player_id) as total_players,
                COUNT(DISTINCT game_id) as total_games,
                SUM(total_games_played) as total_matches_played,
                AVG(win_ratio) as average_win_ratio,
                AVG(rating) as average_rating,
                MAX(last_played) as last_activity
            FROM player_game_stats
        """)

        result = db.execute(query)
        summary = dict(zip(result.keys(), result.fetchone()))

        # Get top games by player count
        top_games_query = text("""
            SELECT 
                game_name,
                COUNT(DISTINCT player_id) as player_count,
                AVG(rating) as avg_rating
            FROM player_game_stats
            GROUP BY game_name
            ORDER BY player_count DESC
            LIMIT 5
        """)

        top_games_result = db.execute(top_games_query)
        summary['top_games'] = [dict(zip(top_games_result.keys(), row))
                                for row in top_games_result.fetchall()]

        return summary
    except Exception as e:
        print(f"Error: {str(e)}")
        raise HTTPException(status_code=500, detail="Error retrieving summary statistics")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
