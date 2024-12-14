-- First, drop all tables in the correct order to handle foreign key constraints
DROP TABLE IF EXISTS player_game_stats;
DROP TABLE IF EXISTS match_history;
DROP TABLE IF EXISTS players;
DROP TABLE IF EXISTS games;

-- Enable UUID generation
SET GLOBAL log_bin_trust_function_creators = 1;

-- Create UUID generation function if it doesn't exist
DELIMITER //
CREATE FUNCTION IF NOT EXISTS UUID_TO_BIN(uuid_str VARCHAR(36))
RETURNS BINARY(16)
DETERMINISTIC
BEGIN
    RETURN UNHEX(REPLACE(uuid_str, '-', ''));
END //
DELIMITER ;

-- Players table with improved demographics
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

-- Games table with focused game types
CREATE TABLE games (
    game_id BINARY(16) PRIMARY KEY,
    name VARCHAR(50) NOT NULL,
    description TEXT NOT NULL,
    rules TEXT NOT NULL,
    can_draw BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Match history table with detailed game statistics
CREATE TABLE match_history (
    match_id BINARY(16) PRIMARY KEY,
    game_id BINARY(16) NOT NULL,
    game_name VARCHAR(50) NOT NULL,
    player1_id BINARY(16) NOT NULL,
    player2_id BINARY(16) NOT NULL,
    winner_id BINARY(16),
    start_time TIMESTAMP NOT NULL,
    end_time TIMESTAMP NOT NULL,
    duration_minutes INT NOT NULL,
    player1_moves INT NOT NULL,
    player2_moves INT NOT NULL,
    result ENUM('win', 'loss', 'draw') NOT NULL,
    FOREIGN KEY (game_id) REFERENCES games(game_id),
    FOREIGN KEY (player1_id) REFERENCES players(player_id),
    FOREIGN KEY (player2_id) REFERENCES players(player_id),
    FOREIGN KEY (winner_id) REFERENCES players(player_id)
);

-- Player game statistics table
CREATE TABLE player_game_stats (
    stat_id BINARY(16) PRIMARY KEY,
    player_id BINARY(16) NOT NULL,
    player_name VARCHAR(100) NOT NULL,
    age INT NOT NULL,
    gender ENUM('Male', 'Female', 'Non-Binary') NOT NULL,
    country VARCHAR(100) NOT NULL,
    game_id BINARY(16) NOT NULL,
    game_name VARCHAR(50) NOT NULL,
    total_games_played INT NOT NULL DEFAULT 0,
    total_wins INT NOT NULL DEFAULT 0,
    total_losses INT NOT NULL DEFAULT 0,
    total_moves INT NOT NULL DEFAULT 0,
    total_time_played_minutes INT NOT NULL DEFAULT 0,
    result VARCHAR(20),
    FOREIGN KEY (player_id) REFERENCES players(player_id),
    FOREIGN KEY (game_id) REFERENCES games(game_id),
    UNIQUE KEY unique_player_game (player_id, game_id)
);
