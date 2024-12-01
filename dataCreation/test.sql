DROP TABLE IF EXISTS games, players, player_game_stats, match_history;

-- Games Table
CREATE TABLE games (
    game_id SERIAL PRIMARY KEY,
    game_name VARCHAR(50) NOT NULL,
    game_type VARCHAR(50),
    max_players INT,
    complexity_level INT
);

-- Insert 11 Games (Battleship + 10 Others)
INSERT INTO games (game_name, game_type, max_players, complexity_level) VALUES
('Battleship', 'Strategy', 2, 3),
('Chess', 'Strategy', 2, 5),
('Connect Four', 'Strategy', 2, 2),
('Tic Tac Toe', 'Strategy', 2, 1),
('Monopoly', 'Economic', 8, 4),
('Risk', 'Strategy', 6, 4),
('Settlers of Catan', 'Resource Management', 4, 3),
('Scrabble', 'Word Game', 4, 3),
('Ticket to Ride', 'Route Building', 5, 3),
('Pandemic', 'Cooperative', 4, 4),
('Carcassonne', 'Tile Placement', 5, 3);

-- Players Table (1000 players)
CREATE TABLE players (
    player_id SERIAL PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    age INT,
    gender VARCHAR(20),
    location VARCHAR(100),
    skill_rating FLOAT DEFAULT 1500,
    registration_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Player Game Statistics Table
CREATE TABLE player_game_stats (
    stat_id SERIAL PRIMARY KEY,
    player_id INT REFERENCES players(player_id),
    game_id INT REFERENCES games(game_id),
    total_games_played INT DEFAULT 0,
    wins INT DEFAULT 0,
    losses INT DEFAULT 0,
    draws INT DEFAULT 0,
    total_moves INT DEFAULT 0,
    total_time_played_seconds INT DEFAULT 0,
    highest_score INT DEFAULT 0,
    win_ratio FLOAT DEFAULT 0.0,
    last_played TIMESTAMP
);

-- Match History Table
CREATE TABLE match_history (
    match_id SERIAL PRIMARY KEY,
    game_id INT REFERENCES games(game_id),
    player1_id INT REFERENCES players(player_id),
    player2_id INT REFERENCES players(player_id),
    winner_id INT,
    start_time TIMESTAMP,
    end_time TIMESTAMP,
    duration_seconds INT,
    moves_count INT,
    game_result VARCHAR(20)
);

-- Data Generation Functions
CREATE OR REPLACE FUNCTION generate_usernames(count INT)
RETURNS TABLE(username VARCHAR, email VARCHAR) AS $$
BEGIN
    RETURN QUERY
    SELECT
        ('player_' || generate_series)::VARCHAR(50),
        ('player_' || generate_series || '@example.com')::VARCHAR(100)
    FROM generate_series(1, count);
END;
$$ LANGUAGE plpgsql;

-- Insert 1000 Players
INSERT INTO players (username, email, age, gender, location)
SELECT
    u.username,
    u.email,
    FLOOR(RANDOM() * 50 + 18)::INT,
    (ARRAY['Male', 'Female', 'Other'])[FLOOR(RANDOM() * 3) + 1],
    (ARRAY['USA', 'Canada', 'UK', 'Australia', 'Germany', 'France',
           'Brazil', 'Japan', 'India', 'China'])[FLOOR(RANDOM() * 10) + 1]
FROM generate_usernames(1000) u;

-- Generate Player Game Statistics
INSERT INTO player_game_stats (player_id, game_id)
SELECT p.player_id, g.game_id
FROM players p
CROSS JOIN games g;

UPDATE player_game_stats
SET
    total_games_played = FLOOR(RANDOM() * 100),
    wins = FLOOR(RANDOM() * 50),
    losses = FLOOR(RANDOM() * 50),
    draws = FLOOR(RANDOM() * 20),
    total_moves = FLOOR(RANDOM() * 1000),
    total_time_played_seconds = FLOOR(RANDOM() * 36000),
    highest_score = FLOOR(RANDOM() * 1000),
    win_ratio = RANDOM(),
    last_played = NOW() - (RANDOM() * INTERVAL '365 days')

WHERE RANDOM() < 0.7;  -- This will update only about 70% of the records


-- Generate Match History
INSERT INTO match_history (
    game_id,
    player1_id,
    player2_id,
    winner_id,
    start_time,
    end_time,
    duration_seconds,
    moves_count,
    game_result
)
SELECT
    FLOOR(RANDOM() * 11 + 1),
    p1.player_id,
    p2.player_id,
    CASE WHEN RANDOM() < 0.1 THEN NULL ELSE
        CASE WHEN RANDOM() < 0.5 THEN p1.player_id ELSE p2.player_id END
    END,
    NOW() - (RANDOM() * INTERVAL '365 days'),
    NOW() - (RANDOM() * INTERVAL '364 days'),
    FLOOR(RANDOM() * 3600),
    FLOOR(RANDOM() * 100),
    CASE WHEN RANDOM() < 0.1 THEN 'Draw' ELSE 'Win' END
FROM
    (SELECT player_id FROM players ORDER BY RANDOM() LIMIT 1000) p1
JOIN
    (SELECT player_id FROM players ORDER BY RANDOM() LIMIT 1000) p2 ON p1.player_id != p2.player_id;


-- Performance Indexes
CREATE INDEX idx_player_game_stats_player ON player_game_stats(player_id);
CREATE INDEX idx_match_history_players ON match_history(player1_id, player2_id);


---------------------------------------------------------------------------------------------
-- -- Create enum for game categories
-- CREATE TYPE game_category AS ENUM ('Strategy', 'Card', 'Classic', 'Puzzle', 'Word');
--
-- -- Games Table with more detailed information
-- CREATE TABLE games (
--     game_id SERIAL PRIMARY KEY,
--     game_name VARCHAR(50) UNIQUE NOT NULL,
--     category game_category,
--     description TEXT,
--     max_players INT,
--     avg_duration_minutes INT,
--     difficulty_level VARCHAR(20),
--     release_date DATE DEFAULT CURRENT_DATE
-- );
--
-- -- Players Table with enhanced demographics
-- CREATE TABLE players (
--     player_id SERIAL PRIMARY KEY,
--     username VARCHAR(50) UNIQUE NOT NULL,
--     email VARCHAR(100) UNIQUE NOT NULL,
--     age INT,
--     gender VARCHAR(20),
--     location VARCHAR(100),
--     preferred_category game_category,
--     premium_member BOOLEAN DEFAULT false,
--     registration_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
--     last_login TIMESTAMP
-- );
--
-- -- Player Game Statistics Table
-- CREATE TABLE player_game_stats (
--     stat_id SERIAL PRIMARY KEY,
--     player_id INT REFERENCES players(player_id),
--     game_id INT REFERENCES games(game_id),
--     total_games_played INT DEFAULT 0,
--     wins INT DEFAULT 0,
--     losses INT DEFAULT 0,
--     draws INT DEFAULT 0,
--     total_moves INT DEFAULT 0,
--     total_time_played_minutes INT DEFAULT 0,
--     highest_score INT DEFAULT 0,
--     win_ratio FLOAT DEFAULT 0.0,
--     last_played TIMESTAMP,
--     UNIQUE(player_id, game_id)
-- );
--
-- -- Match History Table
-- CREATE TABLE match_history (
--     match_id SERIAL PRIMARY KEY,
--     game_id INT REFERENCES games(game_id),
--     player1_id INT REFERENCES players(player_id),
--     player2_id INT REFERENCES players(player_id),
--     winner_id INT REFERENCES players(player_id),
--     start_time TIMESTAMP,
--     end_time TIMESTAMP,
--     duration_minutes INT,
--     moves_count INT,
--     game_result VARCHAR(20)
-- );
--
-- -- Insert Games Data
-- INSERT INTO games (game_name, category, description, max_players, avg_duration_minutes, difficulty_level)
-- VALUES
--     ('Battleship', 'Strategy', 'Classic naval combat game where players try to sink each other''s fleet', 2, 20, 'Intermediate'),
--     ('Chess', 'Strategy', 'Traditional board game of tactical warfare', 2, 30, 'Advanced'),
--     ('Checkers', 'Strategy', 'Classic diagonal movement capture game', 2, 15, 'Beginner'),
--     ('Connect Four', 'Strategy', 'Vertical game of four-in-a-row', 2, 10, 'Beginner'),
--     ('Go Fish', 'Card', 'Family card game of matching pairs', 4, 15, 'Beginner'),
--     ('Memory Match', 'Puzzle', 'Card matching memory game', 2, 10, 'Beginner'),
--     ('Word Hunt', 'Word', 'Find hidden words in a letter grid', 4, 15, 'Intermediate'),
--     ('Tic Tac Toe', 'Classic', 'Get three in a row to win', 2, 5, 'Beginner'),
--     ('Dots and Boxes', 'Classic', 'Connect dots to create boxes', 2, 15, 'Intermediate'),
--     ('Hangman', 'Word', 'Guess the word before the hangman is complete', 2, 10, 'Beginner'),
--     ('Reversi', 'Strategy', 'Flip opponent''s pieces to your color', 2, 20, 'Advanced');
--
-- -- Generate 1000 Players with Random Data
-- DO $$
-- BEGIN
--     FOR i IN 1..1000 LOOP
--         INSERT INTO players (
--             username,
--             email,
--             age,
--             gender,
--             location,
--             preferred_category,
--             premium_member,
--             registration_date,
--             last_login
--         )
--         VALUES (
--             'player_' || i,
--             'player_' || i || '@example.com',
--             floor(random() * (70-13+1) + 13),
--             (ARRAY['Male', 'Female', 'Other'])[floor(random() * 3 + 1)],
--             (ARRAY['USA', 'Canada', 'UK', 'Germany', 'France', 'Japan', 'Australia', 'Brazil', 'India', 'Spain'])[floor(random() * 10 + 1)],
--             (ARRAY['Strategy', 'Card', 'Classic', 'Puzzle', 'Word']::game_category[])[floor(random() * 5 + 1)],
--             random() < 0.3,
--             CURRENT_TIMESTAMP - (random() * 365 * INTERVAL '1 day'),
--             CURRENT_TIMESTAMP - (random() * 30 * INTERVAL '1 day')
--         );
--     END LOOP;
-- END $$;
--
-- -- Generate Player Game Statistics for each player across all games
-- INSERT INTO player_game_stats (
--     player_id,
--     game_id,
--     total_games_played,
--     wins,
--     losses,
--     draws,
--     total_moves,
--     total_time_played_minutes,
--     highest_score,
--     win_ratio,
--     last_played
-- )
-- SELECT
--     p.player_id,
--     g.game_id,
--     floor(random() * 200 + 1)::int as total_games,
--     floor(random() * 100)::int as wins,
--     floor(random() * 100)::int as losses,
--     floor(random() * 20)::int as draws,
--     floor(random() * 1000 + 100)::int as total_moves,
--     floor(random() * 3000 + 60)::int as total_time,
--     floor(random() * 1000)::int as highest_score,
--     round(random()::numeric, 2) as win_ratio,
--     CURRENT_TIMESTAMP - (random() * 30 * INTERVAL '1 day') as last_played
-- FROM
--     players p
-- CROSS JOIN
--     games g;
--
-- -- Generate Match History (recent 1000 matches across all games)
-- INSERT INTO match_history (
--     game_id,
--     player1_id,
--     player2_id,
--     winner_id,
--     start_time,
--     end_time,
--     duration_minutes,
--     moves_count,
--     game_result
-- )
-- SELECT
--     g.game_id,
--     p1.player_id as player1_id,
--     p2.player_id as player2_id,
--     CASE WHEN random() < 0.1 THEN NULL
--          ELSE (ARRAY[p1.player_id, p2.player_id])[floor(random() * 2 + 1)]
--     END as winner_id,
--     start_time,
--     start_time + (floor(random() * 60 + 10) * INTERVAL '1 minute') as end_time,
--     floor(random() * 45 + 5)::int as duration_minutes,
--     floor(random() * 100 + 10)::int as moves_count,
--     (ARRAY['Win', 'Loss', 'Draw'])[floor(random() * 3 + 1)] as game_result
-- FROM
--     games g
-- CROSS JOIN (
--     SELECT
--         player_id,
--         CURRENT_TIMESTAMP - (random() * 30 * INTERVAL '1 day') as start_time
--     FROM players
--     ORDER BY random()
--     LIMIT 1000
-- ) p1
-- CROSS JOIN (
--     SELECT player_id
--     FROM players
--     ORDER BY random()
--     LIMIT 1000
-- ) p2
-- WHERE p1.player_id != p2.player_id
-- LIMIT 1000;
--
-- -- Create indexes for better query performance
-- CREATE INDEX idx_player_game_stats_player_game ON player_game_stats(player_id, game_id);
-- CREATE INDEX idx_match_history_players ON match_history(player1_id, player2_id);
-- CREATE INDEX idx_match_history_game ON match_history(game_id);
-- CREATE INDEX idx_match_history_dates ON match_history(start_time, end_time);
-- CREATE INDEX idx_player_registration ON players(registration_date);