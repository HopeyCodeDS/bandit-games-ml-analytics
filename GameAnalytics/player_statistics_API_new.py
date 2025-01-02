from fastapi import FastAPI, HTTPException, Query, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Database configuration remains the same
DB_USER = os.getenv('DB_USER')
DB_PASSWORD = os.getenv('DB_PASSWORD')
DB_HOST = os.getenv('DB_HOST', 'localhost')
DB_PORT = os.getenv('DB_PORT', '3306')
DB_NAME = 'platform_analytics'

DATABASE_URL = f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}?charset=utf8mb4"
engine = create_engine(DATABASE_URL, pool_pre_ping=True)

app = FastAPI(
    title="Player Statistics API",
    description="API for retrieving player game statistics for dashboard",
    version="1.0.2"
)

origins = [
    "http://localhost.tiangolo.com",
    "http://localhost",
    "http://localhost:8080",
    "http://localhost:3000",
    "http://localhost:5173",
    "*",
]

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Updated Pydantic model
class PlayerStats(BaseModel):
    player_name: str
    game_name: str
    total_games_played: int
    total_wins: int
    total_losses: int
    total_moves: int
    total_time_played_minutes: int
    win_ratio: float
    age: int
    gender: str
    country: str

    class Config:
        from_attributes = True

# Database dependency
def get_db():
    db = Session(engine)
    try:
        yield db
    finally:
        db.close()

# Updated API Endpoints
@app.get("/")
async def root():
    return {
        "message": "Player Statistics API",
        "version": "1.0.2",
        "endpoints": [
            "/api/stats/players",
            "/api/stats/game/{game_name}",
            "/api/stats/country/{country}",
            "/api/stats/most-played-games",
            "/api/stats/top-players/{game_name}"
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
                CONCAT(p.firstname, ' ', p.lastname) as player_name,
                g.name as game_name,
                pgs.total_games_played,
                pgs.total_wins,
                pgs.total_losses,
                pgs.total_moves,
                pgs.total_time_played_minutes,
                pgs.win_ratio,
                TIMESTAMPDIFF(YEAR, p.birthdate, CURRENT_DATE) as age,
                p.gender,
                p.country
            FROM player_game_stats pgs
            JOIN players p ON pgs.player_id = p.player_id
            JOIN games g ON pgs.game_id = g.game_id
            ORDER BY pgs.last_played DESC
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

@app.get("/api/stats/game/{game_name}", response_model=List[PlayerStats])
async def get_game_stats(
        game_name: str,
        db: Session = Depends(get_db)
):
    """
    Get all player statistics for a specific game.
    """
    try:
        # Convert search term to lowercase for consistent matching
        search_term = game_name.lower()

        query = text("""
                SELECT 
                    CONCAT(p.firstname, ' ', p.lastname) as player_name,
                    g.name as game_name,
                    pgs.total_games_played,
                    pgs.total_wins,
                    pgs.total_losses,
                    pgs.total_moves,
                    pgs.total_time_played_minutes,
                    pgs.win_ratio,
                    TIMESTAMPDIFF(YEAR, p.birthdate, CURRENT_DATE) as age,
                    p.gender,
                    p.country
                FROM player_game_stats pgs
                JOIN players p ON pgs.player_id = p.player_id
                JOIN games g ON pgs.game_id = g.game_id
                WHERE LOWER(g.name) LIKE :search_term
                ORDER BY pgs.win_ratio DESC, pgs.total_games_played DESC
            """)

        result = db.execute(query, {"search_term": f"%{search_term}%"})
        stats = [dict(zip(result.keys(), row)) for row in result.fetchall()]

        if not stats:
            raise HTTPException(status_code=404, detail=f"No games found matching '{game_name}'")

        return stats
    except Exception as e:
        print(f"Error: {str(e)}")
        raise HTTPException(status_code=500, detail="Error retrieving game statistics")


@app.get("/api/stats/search/player/{player_name}", response_model=List[PlayerStats])
async def search_by_player_name(
        player_name: str,
        db: Session = Depends(get_db)
):
    """
    Search players by player name (case sensitive).
    """
    try:
        # Convert search term to lowercase for consistent matching
        search_term = player_name.lower()

        query = text("""
            SELECT 
                CONCAT(p.firstname, ' ', p.lastname) as player_name,
                g.name as game_name,
                pgs.total_games_played,
                pgs.total_wins,
                pgs.total_losses,
                pgs.total_moves,
                pgs.total_time_played_minutes,
                pgs.win_ratio,
                TIMESTAMPDIFF(YEAR, p.birthdate, CURRENT_DATE) as age,
                p.gender,
                p.country
            FROM player_game_stats pgs
            JOIN players p ON pgs.player_id = p.player_id
            JOIN games g ON pgs.game_id = g.game_id
            WHERE LOWER(CONCAT(p.firstname, ' ', p.lastname)) LIKE :search_term
            ORDER BY pgs.win_ratio DESC, pgs.total_games_played DESC
        """)

        result = db.execute(query, {"search_term": f"%{search_term}%"})
        stats = [dict(zip(result.keys(), row)) for row in result.fetchall()]

        if not stats:
            raise HTTPException(status_code=404, detail=f"No players found matching '{player_name}'")

        return stats
    except Exception as e:
        print(f"Error: {str(e)}")
        raise HTTPException(status_code=500, detail="Error searching for player")
@app.get("/api/stats/most-played-games")
async def get_most_played_games(
    limit: int = Query(10, ge=1, le=50, description="Number of games to return"),
    db: Session = Depends(get_db)
):
    """
    Get the most played games ranked by total matches played.
    """
    try:
        query = text("""
            SELECT 
                g.name as game_name,
                COUNT(DISTINCT pgs.player_id) as unique_players,
                SUM(pgs.total_games_played) as total_matches,
                AVG(pgs.win_ratio) as average_win_ratio
            FROM player_game_stats pgs
            JOIN games g ON pgs.game_id = g.game_id
            GROUP BY g.name
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

@app.get("/api/stats/top-players/{game_name}", response_model=List[PlayerStats])
async def get_top_players_by_game(
    game_name: str,
    limit: int = Query(3, ge=1, le=10, description="Number of top players to return"),
    db: Session = Depends(get_db)
):
    """
    Get the top players for a specific game, ranked by win ratio and total games played.
    """
    try:
        query = text("""
            SELECT 
                CONCAT(p.firstname, ' ', p.lastname) as player_name,
                g.name as game_name,
                pgs.total_games_played,
                pgs.total_wins,
                pgs.total_losses,
                pgs.total_moves,
                pgs.total_time_played_minutes,
                pgs.win_ratio,
                TIMESTAMPDIFF(YEAR, p.birthdate, CURRENT_DATE) as age,
                p.gender,
                p.country
            FROM player_game_stats pgs
            JOIN players p ON pgs.player_id = p.player_id
            JOIN games g ON pgs.game_id = g.game_id
            WHERE g.name = :game_name
            ORDER BY pgs.win_ratio DESC, pgs.total_games_played DESC
            LIMIT :limit
        """)

        result = db.execute(query, {"game_name": game_name, "limit": limit})
        players = [dict(zip(result.keys(), row)) for row in result.fetchall()]

        if not players:
            raise HTTPException(status_code=404, detail=f"No players found for game {game_name}")

        return players
    except Exception as e:
        print(f"Error: {str(e)}")
        raise HTTPException(status_code=500, detail="Error retrieving top players")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)