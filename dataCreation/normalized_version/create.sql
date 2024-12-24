-- Drop existing tables in correct order
DROP TABLE IF EXISTS player_ratings;
DROP TABLE IF EXISTS match_moves;
DROP TABLE IF EXISTS match_history;
DROP TABLE IF EXISTS player_game_stats;
DROP TABLE IF EXISTS players;
DROP TABLE IF EXISTS games;

-- Enable UUID generation
SET GLOBAL log_bin_trust_function_creators = 1;

-- UUID generation function
DELIMITER //
CREATE FUNCTION IF NOT EXISTS UUID_TO_BIN(uuid_str VARCHAR(36))
RETURNS BINARY(16)
DETERMINISTIC
BEGIN
    RETURN UNHEX(REPLACE(uuid_str, '-', ''));
END //
DELIMITER ;

-- Players table (normalized player information)
CREATE TABLE players (
    player_id BINARY(16) PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    firstname VARCHAR(50) NOT NULL,
    lastname VARCHAR(50) NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    birthdate DATE NOT NULL,
    gender ENUM('Male', 'Female', 'Non-Binary') NOT NULL,
    country VARCHAR(100) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Games table (normalized game information)
CREATE TABLE games (
    game_id BINARY(16) PRIMARY KEY,
    name VARCHAR(50) UNIQUE NOT NULL,
    description TEXT NOT NULL,
    rules TEXT NOT NULL,
    can_draw BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Match history table (normalized match data)
CREATE TABLE match_history (
    match_id BINARY(16) PRIMARY KEY,
    game_id BINARY(16) NOT NULL,
    player1_id BINARY(16) NOT NULL,
    player2_id BINARY(16) NOT NULL,
    winner_id BINARY(16),
    start_time TIMESTAMP NOT NULL,
    end_time TIMESTAMP NOT NULL,
    duration_minutes INT NOT NULL,
    result ENUM('win', 'loss', 'draw') NOT NULL,
    FOREIGN KEY (game_id) REFERENCES games(game_id),
    FOREIGN KEY (player1_id) REFERENCES players(player_id),
    FOREIGN KEY (player2_id) REFERENCES players(player_id),
    FOREIGN KEY (winner_id) REFERENCES players(player_id)
);

-- Match moves table (normalized move data)
CREATE TABLE match_moves (
    move_id BINARY(16) PRIMARY KEY,
    match_id BINARY(16) NOT NULL,
    player_id BINARY(16) NOT NULL,
    moves_count INT NOT NULL,
    FOREIGN KEY (match_id) REFERENCES match_history(match_id),
    FOREIGN KEY (player_id) REFERENCES players(player_id)
);

-- Player game statistics table (normalized statistics)
CREATE TABLE player_game_stats (
    stat_id BINARY(16) PRIMARY KEY,
    player_id BINARY(16) NOT NULL,
    game_id BINARY(16) NOT NULL,
    total_games_played INT NOT NULL DEFAULT 0,
    total_wins INT NOT NULL DEFAULT 0,
    total_losses INT NOT NULL DEFAULT 0,
    total_draws INT NOT NULL DEFAULT 0,
    total_moves INT NOT NULL DEFAULT 0,
    total_time_played_minutes INT NOT NULL DEFAULT 0,
    win_ratio DECIMAL(5,2) GENERATED ALWAYS AS (
        CASE
            WHEN total_games_played = 0 THEN 0.00
            ELSE (total_wins * 100.0 / total_games_played)
        END
    ) STORED,
    last_played TIMESTAMP,
    -- ML target variables
    is_churned BOOLEAN DEFAULT FALSE,                                  -- Target for churn prediction
    engagement_level DECIMAL(5,2) DEFAULT 0.00,                        -- Target for engagement prediction (0-100)
    player_level ENUM('novice', 'intermediate', 'expert') DEFAULT 'novice',  -- Target for player classification
    win_probability DECIMAL(5,4) DEFAULT 0.5000,                       -- Predicted probability of winning next game (0-1)
    -- Constraints
    FOREIGN KEY (player_id) REFERENCES players(player_id),
    FOREIGN KEY (game_id) REFERENCES games(game_id),
    UNIQUE KEY unique_player_game (player_id, game_id)
);

-- Player ratings table (normalized rating data)
CREATE TABLE player_ratings (
    rating_id BINARY(16) PRIMARY KEY,
    player_id BINARY(16) NOT NULL,
    game_id BINARY(16) NOT NULL,
    rating TINYINT CHECK (rating >= 1 AND rating <= 5),
    rating_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (player_id) REFERENCES players(player_id),
    FOREIGN KEY (game_id) REFERENCES games(game_id)
);

-- Create indexes for common queries
CREATE INDEX idx_match_history_game ON match_history(game_id);
CREATE INDEX idx_match_history_players ON match_history(player1_id, player2_id);
CREATE INDEX idx_match_history_winner ON match_history(winner_id);
CREATE INDEX idx_match_moves_match ON match_moves(match_id);
CREATE INDEX idx_player_game_stats_player ON player_game_stats(player_id);
CREATE INDEX idx_player_ratings_player_game ON player_ratings(player_id, game_id);
-- Simple index for ML-related queries
CREATE INDEX idx_player_game_stats_ml ON player_game_stats(is_churned, engagement_level, player_level);