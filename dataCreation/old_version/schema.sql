DROP TABLE IF EXISTS games, players, player_game_stats, match_history, game_category;

-- Create schema and types
CREATE TYPE game_category AS ENUM ('Strategy', 'Card', 'Classic', 'Puzzle', 'Word');

-- Base tables
CREATE TABLE games (
    game_id SERIAL PRIMARY KEY,
    game_name VARCHAR(50) UNIQUE NOT NULL,
    category game_category,
    description TEXT,
    max_players INT,
    avg_duration_minutes INT,
    difficulty_level VARCHAR(20),
    release_date DATE DEFAULT CURRENT_DATE
);

CREATE TABLE players (
    player_id SERIAL PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    age INT,
    gender VARCHAR(20),
    location VARCHAR(100),
    preferred_category game_category,
    premium_member BOOLEAN DEFAULT false,
    registration_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_login TIMESTAMP
);

CREATE TABLE player_game_stats (
    stat_id SERIAL PRIMARY KEY,
    player_id INT REFERENCES players(player_id),
    game_id INT REFERENCES games(game_id),
    total_games_played INT DEFAULT 0,
    wins INT DEFAULT 0,
    losses INT DEFAULT 0,
    draws INT DEFAULT 0,
    total_moves INT DEFAULT 0,
    total_time_played_minutes INT DEFAULT 0,
    highest_score INT DEFAULT 0,
    win_ratio FLOAT DEFAULT 0.0,
    last_played TIMESTAMP,
    UNIQUE(player_id, game_id)
);

CREATE TABLE match_history (
    match_id SERIAL PRIMARY KEY,
    game_id INT REFERENCES games(game_id),
    player1_id INT REFERENCES players(player_id),
    player2_id INT REFERENCES players(player_id),
    winner_id INT REFERENCES players(player_id),
    start_time TIMESTAMP,
    end_time TIMESTAMP,
    duration_minutes INT,
    moves_count INT,
    game_result VARCHAR(20)
);

-- Insert base game data
INSERT INTO games (game_name, category, description, max_players, avg_duration_minutes, difficulty_level)
VALUES
    ('Battleship', 'Strategy', 'Classic naval combat game', 2, 20, 'Intermediate'),
    ('Chess', 'Strategy', 'Traditional board game of tactical warfare', 2, 30, 'Advanced'),
    ('Checkers', 'Strategy', 'Classic diagonal movement capture game', 2, 15, 'Beginner'),
    ('Connect Four', 'Strategy', 'Vertical game of four-in-a-row', 2, 10, 'Beginner'),
    ('Go Fish', 'Card', 'Family card game of matching pairs', 4, 15, 'Beginner'),
    ('Memory Match', 'Puzzle', 'Card matching memory game', 2, 10, 'Beginner'),
    ('Word Hunt', 'Word', 'Find hidden words in a letter grid', 4, 15, 'Intermediate'),
    ('Tic Tac Toe', 'Classic', 'Get three in a row to win', 2, 5, 'Beginner'),
    ('Dots and Boxes', 'Classic', 'Connect dots to create boxes', 2, 15, 'Intermediate'),
    ('Hangman', 'Word', 'Guess the word before the hangman is complete', 2, 10, 'Beginner');

-- Generate consistent player data
DO $$
DECLARE
    player_count INT := 1000;
BEGIN
    -- Insert players
    FOR i IN 1..player_count LOOP
        INSERT INTO players (
            username,
            email,
            age,
            gender,
            location,
            preferred_category,
            premium_member,
            registration_date,
            last_login
        )
        VALUES (
            'player_' || i,
            'player_' || i || '@example.com',
            floor(random() * (70-13+1) + 13),
            (ARRAY['Male', 'Female', 'Other'])[floor(random() * 3 + 1)],
            (ARRAY['USA', 'Canada', 'UK', 'Germany', 'France', 'Japan', 'Australia', 'Brazil', 'India', 'Spain'])[floor(random() * 10 + 1)],
            (ARRAY['Strategy', 'Card', 'Classic', 'Puzzle', 'Word']::game_category[])[floor(random() * 5 + 1)],
            random() < 0.3,
            CURRENT_TIMESTAMP - (random() * 365 * INTERVAL '1 day'),
            CURRENT_TIMESTAMP - (random() * 30 * INTERVAL '1 day')
        );
    END LOOP;
END $$;

-- Function to generate consistent match history and stats
CREATE OR REPLACE FUNCTION generate_consistent_game_data() RETURNS void AS $$
DECLARE
    games_per_player INT;
    total_matches INT;
    current_player_id INT;
    opponent_id INT;
    current_game_id INT;
    match_start TIMESTAMP;
    match_duration INT;
    winner_id INT;
BEGIN
    -- For each player
    FOR current_player_id IN 1..1000 LOOP
        -- For each game
        FOR current_game_id IN 1..10 LOOP
            -- Randomly decide how many matches this player plays of this game (10-50)
            games_per_player := floor(random() * 41 + 10);

            -- Initialize counters for player_game_stats
            total_matches := 0;

            -- Generate matches
            FOR i IN 1..games_per_player LOOP
                -- Select random opponent (different from current player)
                SELECT player_id INTO opponent_id
                FROM players
                WHERE player_id != current_player_id
                ORDER BY random()
                LIMIT 1;

                -- Generate match details
                match_start := CURRENT_TIMESTAMP - (random() * 365 * INTERVAL '1 day');
                match_duration := floor(random() * 45 + 5);

                -- Determine winner
                IF random() < 0.5 THEN
                    winner_id := current_player_id;
                ELSE
                    winner_id := opponent_id;
                END IF;

                -- Insert match record
                INSERT INTO match_history (
                    game_id,
                    player1_id,
                    player2_id,
                    winner_id,
                    start_time,
                    end_time,
                    duration_minutes,
                    moves_count,
                    game_result
                ) VALUES (
                    current_game_id,
                    current_player_id,
                    opponent_id,
                    winner_id,
                    match_start,
                    match_start + (match_duration * INTERVAL '1 minute'),
                    match_duration,
                    floor(random() * 100 + 10),
                    CASE
                        WHEN winner_id = current_player_id THEN 'Win'
                        WHEN winner_id = opponent_id THEN 'Loss'
                        ELSE 'Draw'
                    END
                );

                total_matches := total_matches + 1;
            END LOOP;

            -- Calculate and insert player_game_stats
            INSERT INTO player_game_stats (
                player_id,
                game_id,
                total_games_played,
                wins,
                losses,
                draws,
                total_moves,
                total_time_played_minutes,
                win_ratio,
                last_played
            )
            SELECT
                current_player_id,
                current_game_id,
                COUNT(*),
                COUNT(*) FILTER (WHERE game_result = 'Win'),
                COUNT(*) FILTER (WHERE game_result = 'Loss'),
                COUNT(*) FILTER (WHERE game_result = 'Draw'),
                SUM(moves_count),
                SUM(duration_minutes),
                ROUND(COUNT(*) FILTER (WHERE game_result = 'Win')::NUMERIC / COUNT(*)::NUMERIC, 2),
                MAX(end_time)
            FROM match_history
            WHERE game_id = current_game_id
            AND (player1_id = current_player_id OR player2_id = current_player_id);

        END LOOP;
    END LOOP;
END;
$$ LANGUAGE plpgsql;

-- Generate the consistent data
SELECT generate_consistent_game_data();

-- Create indexes for performance
CREATE INDEX idx_player_game_stats_player_game ON player_game_stats(player_id, game_id);
CREATE INDEX idx_match_history_players ON match_history(player1_id, player2_id);
CREATE INDEX idx_match_history_game ON match_history(game_id);
CREATE INDEX idx_match_history_dates ON match_history(start_time, end_time);

