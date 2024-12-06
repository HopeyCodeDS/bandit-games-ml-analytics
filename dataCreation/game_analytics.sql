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

-- Players table
CREATE TABLE players (
    player_id BINARY(16) PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    age INT,
    gender ENUM('MALE', 'FEMALE', 'NON-BINARY', 'OTHER') DEFAULT NULL,
    country VARCHAR(100),
    created_at TIMESTAMP,
    last_login TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE
);

-- Games table
CREATE TABLE games (
    game_id BINARY(16) PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    rules TEXT,
    max_players INT DEFAULT 2,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP,
    updated_at TIMESTAMP
);

-- Matches table
CREATE TABLE matches (
    match_id BINARY(16) PRIMARY KEY,
    game_id BINARY(16),
    player1_id BINARY(16),
    player2_id BINARY(16),
    winner_id BINARY(16),
    start_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    end_time TIMESTAMP,
    duration_minutes INT,
    moves_count INT DEFAULT 0,
    player1_hits INT DEFAULT 0,
    player1_misses INT DEFAULT 0,
    player2_hits INT DEFAULT 0,
    player2_misses INT DEFAULT 0,
    game_state JSON,
    game_result ENUM('WIN', 'LOSS', 'DRAW', 'ABANDONED') DEFAULT NULL,
    FOREIGN KEY (game_id) REFERENCES games(game_id),
    FOREIGN KEY (player1_id) REFERENCES players(player_id),
    FOREIGN KEY (player2_id) REFERENCES players(player_id),
    FOREIGN KEY (winner_id) REFERENCES players(player_id)
);

-- Player Game Statistics
CREATE TABLE player_game_stats (
    stat_id BINARY(16) PRIMARY KEY,
    player_id BINARY(16),
    game_id BINARY(16),
    total_games_played INT DEFAULT 0,
    result ENUM('WIN', 'LOSS', 'DRAW', 'ABANDONED') DEFAULT NULL,
    total_moves INT DEFAULT 0,
    total_hits INT DEFAULT 0,
    total_misses INT DEFAULT 0,
    total_time_played_minutes INT DEFAULT 0,
    highest_score INT DEFAULT 0,
    win_ratio DECIMAL(5,2) DEFAULT 0.00,
    rating TINYINT CHECK (rating >= 1 AND rating <= 5),
    churned ENUM('YES', 'NO'),
    player_level ENUM('Novice', 'Intermediate', 'Expert'),
    last_played TIMESTAMP,
    FOREIGN KEY (player_id) REFERENCES players(player_id),
    FOREIGN KEY (game_id) REFERENCES games(game_id),
    UNIQUE KEY unique_player_game (player_id, game_id)
);

# -- Achievements table
# CREATE TABLE achievements (
#     achievement_id BINARY(16) PRIMARY KEY,
#     game_id BINARY(16),
#     achievement_name VARCHAR(100) NOT NULL,
#     game_name VARCHAR(100) NOT NULL,
#     description TEXT,
#     criteria TEXT,
#     points INT DEFAULT 0,
#     FOREIGN KEY (game_id) REFERENCES games(game_id)
# );
#
# -- Player Achievements
# CREATE TABLE player_achievements (
#     player_id BINARY(16),
#     achievement_id BINARY(16),
#     unlocked_at TIMESTAMP,
#     PRIMARY KEY (player_id, achievement_id),
#     FOREIGN KEY (player_id) REFERENCES players(player_id),
#     FOREIGN KEY (achievement_id) REFERENCES achievements(achievement_id)
# );
#
# -- Friends system
# CREATE TABLE friendships (
#     friendship_id BINARY(16) PRIMARY KEY,
#     requester_id BINARY(16),
#     addressee_id BINARY(16),
#     status ENUM('PENDING', 'ACCEPTED', 'REJECTED', 'BLOCKED') DEFAULT 'PENDING',
#     created_at TIMESTAMP,
#     updated_at TIMESTAMP,
#     FOREIGN KEY (requester_id) REFERENCES players(player_id),
#     FOREIGN KEY (addressee_id) REFERENCES players(player_id),
#     UNIQUE KEY unique_friendship (requester_id, addressee_id)
# );


-- Indexes for better query performance
CREATE INDEX idx_matches_game_id ON matches(game_id);
CREATE INDEX idx_matches_players ON matches(player1_id, player2_id);
CREATE INDEX idx_player_stats_game ON player_game_stats(game_id);
CREATE INDEX idx_player_stats_player ON player_game_stats(player_id);
# CREATE INDEX idx_achievements_game ON achievements(game_id);
# CREATE INDEX idx_friendships_players ON friendships(requester_id, addressee_id);
# CREATE INDEX idx_player_game_rating ON player_game_stats(game_id, rating DESC);



-- Audit Tables and Triggers for Data Changes --

-- Audit tables for players and games
CREATE TABLE players_audit (
    audit_id BINARY(16) PRIMARY KEY,
    player_id BINARY(16),
    action_type ENUM('INSERT', 'UPDATE', 'DELETE') NOT NULL,
    username VARCHAR(50),
    email VARCHAR(100),
    age INT,
    gender ENUM('MALE', 'FEMALE', 'NON-BINARY', 'OTHER'),
    country VARCHAR(100),
    is_active BOOLEAN,
    changed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    changed_by VARCHAR(100)
);

CREATE TABLE games_audit (
    audit_id BINARY(16) PRIMARY KEY,
    game_id BINARY(16),
    action_type ENUM('INSERT', 'UPDATE', 'DELETE') NOT NULL,
    name VARCHAR(100),
    description TEXT,
    rules TEXT,
    max_players INT,
    is_active BOOLEAN,
    changed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    changed_by VARCHAR(100)
);

-- Audit table for player_game_stats
CREATE TABLE player_game_stats_audit (
    audit_id BINARY(16) PRIMARY KEY,
    stat_id BINARY(16),
    player_id BINARY(16),
    game_id BINARY(16),
    action_type ENUM('INSERT', 'UPDATE', 'DELETE') NOT NULL,
    total_games_played INT,
    result ENUM('WIN', 'LOSS', 'DRAW', 'ABANDONED'),
    total_moves INT,
    hits INT,
    misses INT,
    total_time_played_minutes INT,
    highest_score INT,
    win_ratio DECIMAL(5,2),
    rating TINYINT,
    churned ENUM('YES', 'NO'),
    player_level ENUM('Novice', 'Intermediate', 'Expert'),
    last_played TIMESTAMP,
    changed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    changed_by VARCHAR(100)
);


-- Triggers for players table
DELIMITER //

CREATE TRIGGER players_after_insert
AFTER INSERT ON players
FOR EACH ROW
BEGIN
    INSERT INTO players_audit
    SET audit_id = UUID_TO_BIN(UUID()),
        player_id = NEW.player_id,
        action_type = 'INSERT',
        username = NEW.username,
        email = NEW.email,
        age = NEW.age,
        gender = NEW.gender,
        country = NEW.country,
        is_active = NEW.is_active,
        changed_by = USER();
END//

CREATE TRIGGER players_after_update
AFTER UPDATE ON players
FOR EACH ROW
BEGIN
    INSERT INTO players_audit
    SET audit_id = UUID_TO_BIN(UUID()),
        player_id = NEW.player_id,
        action_type = 'UPDATE',
        username = NEW.username,
        email = NEW.email,
        age = NEW.age,
        gender = NEW.gender,
        country = NEW.country,
        is_active = NEW.is_active,
        changed_by = USER();
END//

CREATE TRIGGER players_after_delete
AFTER DELETE ON players
FOR EACH ROW
BEGIN
    INSERT INTO players_audit
    SET audit_id = UUID_TO_BIN(UUID()),
        player_id = OLD.player_id,
        action_type = 'DELETE',
        username = OLD.username,
        email = OLD.email,
        age = OLD.age,
        gender = OLD.gender,
        country = OLD.country,
        is_active = OLD.is_active,
        changed_by = USER();
END//

-- Triggers for games table
CREATE TRIGGER games_after_insert
AFTER INSERT ON games
FOR EACH ROW
BEGIN
    INSERT INTO games_audit
    SET audit_id = UUID_TO_BIN(UUID()),
        game_id = NEW.game_id,
        action_type = 'INSERT',
        name = NEW.name,
        description = NEW.description,
        rules = NEW.rules,
        max_players = NEW.max_players,
        is_active = NEW.is_active,
        changed_by = USER();
END//

CREATE TRIGGER games_after_update
AFTER UPDATE ON games
FOR EACH ROW
BEGIN
    INSERT INTO games_audit
    SET audit_id = UUID_TO_BIN(UUID()),
        game_id = NEW.game_id,
        action_type = 'UPDATE',
        name = NEW.name,
        description = NEW.description,
        rules = NEW.rules,
        max_players = NEW.max_players,
        is_active = NEW.is_active,
        changed_by = USER();
END//

CREATE TRIGGER games_after_delete
AFTER DELETE ON games
FOR EACH ROW
BEGIN
    INSERT INTO games_audit
    SET audit_id = UUID_TO_BIN(UUID()),
        game_id = OLD.game_id,
        action_type = 'DELETE',
        name = OLD.name,
        description = OLD.description,
        rules = OLD.rules,
        max_players = OLD.max_players,
        is_active = OLD.is_active,
        changed_by = USER();
END//

DELIMITER ;

-- Create triggers for player_game_stats table
DELIMITER //

CREATE TRIGGER player_game_stats_after_insert
AFTER INSERT ON player_game_stats
FOR EACH ROW
BEGIN
    INSERT INTO player_game_stats_audit
    SET audit_id = UUID_TO_BIN(UUID()),
        stat_id = NEW.stat_id,
        player_id = NEW.player_id,
        game_id = NEW.game_id,
        action_type = 'INSERT',
        total_games_played = NEW.total_games_played,
        result = NEW.result,
        total_moves = NEW.total_moves,
        total_hits = NEW.total_hits,
        total_misses = NEW.total_misses,
        total_time_played_minutes = NEW.total_time_played_minutes,
        highest_score = NEW.highest_score,
        win_ratio = NEW.win_ratio,
        rating = NEW.rating,
        churned = NEW.churned,
        player_level = NEW.player_level,
        last_played = NEW.last_played,
        changed_by = USER();
END//

CREATE TRIGGER player_game_stats_after_update
AFTER UPDATE ON player_game_stats
FOR EACH ROW
BEGIN
    INSERT INTO player_game_stats_audit
    SET audit_id = UUID_TO_BIN(UUID()),
        stat_id = NEW.stat_id,
        player_id = NEW.player_id,
        game_id = NEW.game_id,
        action_type = 'UPDATE',
        total_games_played = NEW.total_games_played,
        result = NEW.result,
        total_moves = NEW.total_moves,
        total_hits = NEW.total_hits,
        total_misses = NEW.total_misses,
        total_time_played_minutes = NEW.total_time_played_minutes,
        highest_score = NEW.highest_score,
        win_ratio = NEW.win_ratio,
        rating = NEW.rating,
        churned = NEW.churned,
        player_level = NEW.player_level,
        last_played = NEW.last_played,
        changed_by = USER();
END//

CREATE TRIGGER player_game_stats_after_delete
AFTER DELETE ON player_game_stats
FOR EACH ROW
BEGIN
    INSERT INTO player_game_stats_audit
    SET audit_id = UUID_TO_BIN(UUID()),
        stat_id = OLD.stat_id,
        player_id = OLD.player_id,
        game_id = OLD.game_id,
        action_type = 'DELETE',
        total_games_played = OLD.total_games_played,
        result = OLD.result,
        total_moves = OLD.total_moves,
        total_hits = OLD.total_hits,
        total_misses = OLD.total_misses,
        total_time_played_minutes = OLD.total_time_played_minutes,
        highest_score = OLD.highest_score,
        win_ratio = OLD.win_ratio,
        rating = OLD.rating,
        churned = OLD.churned,
        player_level = OLD.player_level,
        last_played = OLD.last_played,
        changed_by = USER();
END//

DELIMITER ;

-- Indexes for audit tables
CREATE INDEX idx_players_audit_player_id ON players_audit(player_id);
CREATE INDEX idx_players_audit_changed_at ON players_audit(changed_at);
CREATE INDEX idx_games_audit_game_id ON games_audit(game_id);
CREATE INDEX idx_games_audit_changed_at ON games_audit(changed_at);

-- Create indexes for the audit table
CREATE INDEX idx_player_game_stats_audit_stat_id ON player_game_stats_audit(stat_id);
CREATE INDEX idx_player_game_stats_audit_player_id ON player_game_stats_audit(player_id);
CREATE INDEX idx_player_game_stats_audit_game_id ON player_game_stats_audit(game_id);
CREATE INDEX idx_player_game_stats_audit_changed_at ON player_game_stats_audit(changed_at);

# --------------------------------------------------------------------------------------------------------------------------------------------------

-- First, insert the games data
INSERT INTO games (game_id, name, description, rules, max_players, is_active) VALUES
(UUID_TO_BIN(UUID()), 'Battleship',
'A strategic guessing game where players attempt to sink their opponent''s fleet of ships.',
'Each player arranges their ships on a grid and takes turns calling out coordinates to find and sink the opponent''s ships. First to sink all ships wins.',
2, TRUE),

(UUID_TO_BIN(UUID()), 'Chess',
'The classic strategy board game of kings and queens.',
'Players move pieces according to specific rules with the goal of checkmating the opponent''s king. Each piece type has unique movement patterns.',
2, TRUE),

(UUID_TO_BIN(UUID()), 'Checkers',
'Traditional board game of diagonal moves and jumps.',
'Players move diagonally and try to capture opponent''s pieces by jumping over them. Kings can move backwards. Capture all pieces or block opponent to win.',
2, TRUE),

(UUID_TO_BIN(UUID()), 'Connect Four',
'Vertical strategy game of getting four tokens in a row.',
'Players take turns dropping colored tokens into a vertical grid. First to connect four tokens horizontally, vertically, or diagonally wins.',
2, TRUE),

(UUID_TO_BIN(UUID()), 'Memory Match',
'Card matching game testing memory and concentration.',
'Cards are laid face down. Players take turns flipping two cards to find matching pairs. Player with most pairs wins.',
4, TRUE),

(UUID_TO_BIN(UUID()), 'Tic Tac Toe',
'Classic game of X''s and O''s.',
'Players take turns marking spaces in a 3×3 grid. First player to align three of their marks horizontally, vertically, or diagonally wins.',
2, TRUE),

(UUID_TO_BIN(UUID()), 'Dots and Boxes',
'Strategic game of connecting dots to form boxes.',
'Players take turns connecting adjacent dots. When a player completes a box, they initial it and get another turn. Most boxes wins.',
4, TRUE),

(UUID_TO_BIN(UUID()), 'Hangman',
'Word guessing game with limited chances.',
'One player thinks of a word, others guess letters. Each wrong guess adds a part to the hangman. Game ends when word is guessed or hangman is complete.',
2, TRUE);

-- Now, create a procedure to generate 1000 unique players
DELIMITER //

CREATE PROCEDURE generate_players()
BEGIN
    DECLARE i INT DEFAULT 0;
    DECLARE username_suffix VARCHAR(10);
    DECLARE email_domain VARCHAR(100);
    DECLARE random_age INT;
    DECLARE random_gender VARCHAR(20);
    DECLARE random_country VARCHAR(100);

    -- Array of common email domains
    SET email_domain = ELT(FLOOR(1 + RAND() * 5),
        '@gmail.com', '@yahoo.com', '@hotmail.com', '@outlook.com', '@icloud.com');

    -- Generate 1000 players
    WHILE i < 1000 DO
        SET username_suffix = LPAD(FLOOR(RAND() * 99999), 5, '0');
        SET random_age = FLOOR(13 + RAND() * 67); -- Ages 13 to 80
        SET random_gender = ELT(FLOOR(1 + RAND() * 4),
            'MALE', 'FEMALE', 'NON-BINARY', 'OTHER');
        SET random_country = ELT(FLOOR(1 + RAND() * 30),
            'USA', 'Canada', 'UK', 'Australia', 'Germany', 'France', 'Spain',
            'Italy', 'Japan', 'South Korea', 'Brazil', 'Mexico', 'India',
            'Russia', 'China', 'Netherlands', 'Sweden', 'Norway', 'Denmark',
            'Finland', 'Ireland', 'New Zealand', 'Singapore', 'Malaysia',
            'Philippines', 'Thailand', 'Vietnam', 'Indonesia', 'South Africa', 'Nigeria');

        -- Generate player names based on patterns
        CASE FLOOR(1 + RAND() * 4)
            WHEN 1 THEN
                -- GamerType_Numbers (e.g., ProGamer_12345)
                INSERT INTO players (player_id, username, email, age, gender, country, last_login)
                VALUES (
                    UUID_TO_BIN(UUID()),
                    CONCAT(
                        ELT(FLOOR(1 + RAND() * 5), 'Pro', 'Elite', 'Epic', 'Master', 'Ultra'),
                        ELT(FLOOR(1 + RAND() * 5), 'Gamer', 'Player', 'Champion', 'Warrior', 'Legend'),
                        '_', username_suffix
                    ),
                    CONCAT('player', username_suffix, email_domain),
                    random_age,
                    random_gender,
                    random_country,
                    DATE_SUB(NOW(), INTERVAL FLOOR(RAND() * 30) DAY)
                );
            WHEN 2 THEN
                -- Cool word combinations (e.g., NightWolf12345)
                INSERT INTO players (player_id, username, email, age, gender, country, last_login)
                VALUES (
                    UUID_TO_BIN(UUID()),
                    CONCAT(
                        ELT(FLOOR(1 + RAND() * 5), 'Night', 'Dark', 'Storm', 'Fire', 'Ice'),
                        ELT(FLOOR(1 + RAND() * 5), 'Wolf', 'Dragon', 'Phoenix', 'Hawk', 'Knight'),
                        username_suffix
                    ),
                    CONCAT('gamer', username_suffix, email_domain),
                    random_age,
                    random_gender,
                    random_country,
                    DATE_SUB(NOW(), INTERVAL FLOOR(RAND() * 30) DAY)
                );
            WHEN 3 THEN
                -- Game-specific names (e.g., ChessMaster12345)
                INSERT INTO players (player_id, username, email, age, gender, country, last_login)
                VALUES (
                    UUID_TO_BIN(UUID()),
                    CONCAT(
                        ELT(FLOOR(1 + RAND() * 8), 'Chess', 'Battle', 'Dots', 'Connect', 'Memory', 'Tic', 'Box', 'Game'),
                        ELT(FLOOR(1 + RAND() * 5), 'Master', 'King', 'Queen', 'Lord', 'Boss'),
                        username_suffix
                    ),
                    CONCAT('gaming', username_suffix, email_domain),
                    random_age,
                    random_gender,
                    random_country,
                    DATE_SUB(NOW(), INTERVAL FLOOR(RAND() * 30) DAY)
                );
            ELSE
                -- Simple format (e.g., Player12345)
                INSERT INTO players (player_id, username, email, age, gender, country, last_login)
                VALUES (
                    UUID_TO_BIN(UUID()),
                    CONCAT(
                        ELT(FLOOR(1 + RAND() * 5), 'Player', 'Gamer', 'User', 'Challenger', 'Champion'),
                        username_suffix
                    ),
                    CONCAT('user', username_suffix, email_domain),
                    random_age,
                    random_gender,
                    random_country,
                    DATE_SUB(NOW(), INTERVAL FLOOR(RAND() * 30) DAY)
                );
        END CASE;

        SET i = i + 1;
    END WHILE;
END //

DELIMITER ;

-- Execute the procedure to generate players
CALL generate_players();

-- Clean up
DROP PROCEDURE IF EXISTS generate_players;

# -------------------------------------------------------------------------------------------------------------------------------------------------------

-- First, let's create temporary tables to store game and player IDs for easier reference
CREATE TEMPORARY TABLE temp_game_ids (
    game_id BINARY(16),
    game_name VARCHAR(100)
);

CREATE TEMPORARY TABLE temp_player_ids (
    player_id BINARY(16)
);

-- Populate temporary tables
INSERT INTO temp_game_ids
SELECT game_id, name FROM games;

INSERT INTO temp_player_ids
SELECT player_id FROM players;

DELIMITER //

CREATE PROCEDURE generate_matches()
BEGIN
    DECLARE i INT DEFAULT 0;
    DECLARE battleship_id BINARY(16);
    DECLARE total_matches INT DEFAULT 3000;
    DECLARE battleship_matches INT DEFAULT 1200; -- 40% of matches are Battleship
    DECLARE current_game_id BINARY(16);
    DECLARE current_game_name VARCHAR(100);
    DECLARE player1_id BINARY(16);
    DECLARE player2_id BINARY(16);
    DECLARE match_duration INT;
    DECLARE start_datetime TIMESTAMP;
    DECLARE game_moves INT;
    DECLARE winner_id BINARY(16);
    DECLARE game_outcome ENUM('WIN', 'LOSS', 'DRAW', 'ABANDONED');

    -- Get Battleship game_id
    SELECT game_id INTO battleship_id
    FROM temp_game_ids
    WHERE game_name = 'Battleship';

    -- Generate matches
    WHILE i < total_matches DO
        -- Select random players
        SELECT player_id INTO player1_id
        FROM temp_player_ids
        ORDER BY RAND()
        LIMIT 1;

        SELECT player_id INTO player2_id
        FROM temp_player_ids
        WHERE player_id != player1_id
        ORDER BY RAND()
        LIMIT 1;

        -- Select game (weighted towards Battleship)
        IF i < battleship_matches THEN
            SET current_game_id = battleship_id;
            SET current_game_name = 'Battleship';
        ELSE
            SELECT game_id, game_name INTO current_game_id, current_game_name
            FROM temp_game_ids
            WHERE game_name != 'Battleship'
            ORDER BY RAND()
            LIMIT 1;
        END IF;

        -- Generate historical timestamp (between 4 years ago and now)
        SET start_datetime = TIMESTAMP(
            DATE_SUB(NOW(),
            INTERVAL FLOOR(RAND() * (4 * 365) + 1) DAY -
            INTERVAL FLOOR(RAND() * 24) HOUR -
            INTERVAL FLOOR(RAND() * 60) MINUTE
        ));

        -- Set game-specific parameters
        CASE current_game_name
            WHEN 'Battleship' THEN
                SET match_duration = 15 + FLOOR(RAND() * 30); -- 15-45 minutes
                SET game_moves = 35 + FLOOR(RAND() * 45); -- 35-80 moves
            WHEN 'Chess' THEN
                SET match_duration = 20 + FLOOR(RAND() * 40); -- 20-60 minutes
                SET game_moves = 30 + FLOOR(RAND() * 40); -- 30-70 moves
            WHEN 'Checkers' THEN
                SET match_duration = 10 + FLOOR(RAND() * 20); -- 10-30 minutes
                SET game_moves = 20 + FLOOR(RAND() * 30); -- 20-50 moves
            WHEN 'Connect Four' THEN
                SET match_duration = 5 + FLOOR(RAND() * 10); -- 5-15 minutes
                SET game_moves = 15 + FLOOR(RAND() * 25); -- 15-40 moves
            WHEN 'Memory Match' THEN
                SET match_duration = 5 + FLOOR(RAND() * 15); -- 5-20 minutes
                SET game_moves = 20 + FLOOR(RAND() * 30); -- 20-50 moves
            WHEN 'Tic Tac Toe' THEN
                SET match_duration = 2 + FLOOR(RAND() * 5); -- 2-7 minutes
                SET game_moves = 5 + FLOOR(RAND() * 4); -- 5-9 moves
            WHEN 'Dots and Boxes' THEN
                SET match_duration = 10 + FLOOR(RAND() * 20); -- 10-30 minutes
                SET game_moves = 25 + FLOOR(RAND() * 35); -- 25-60 moves
            ELSE
                SET match_duration = 10 + FLOOR(RAND() * 20); -- 10-30 minutes
                SET game_moves = 15 + FLOOR(RAND() * 25); -- 15-40 moves
        END CASE;

        -- Determine game outcome (80% completed games, 20% abandoned)
        IF RAND() < 0.2 THEN
            SET game_outcome = 'ABANDONED';
            SET winner_id = NULL;
            -- Reduce duration for abandoned games
            SET match_duration = match_duration * (RAND() * 0.5);
        ELSE
            IF RAND() < 0.1 AND current_game_name IN ('Chess', 'Tic Tac Toe', 'Connect Four') THEN
                SET game_outcome = 'DRAW';
                SET winner_id = NULL;
            ELSE
                SET game_outcome = 'WIN';
                SET winner_id = IF(RAND() < 0.5, player1_id, player2_id);
            END IF;
        END IF;

        -- Insert match data
        INSERT INTO matches (
            match_id, game_id, player1_id, player2_id, winner_id,
            start_time, end_time, duration_minutes, moves_count,
            player1_hits, player1_misses, player2_hits, player2_misses,
            game_state, game_result
        )
        VALUES (
            UUID_TO_BIN(UUID()),
            current_game_id,
            player1_id,
            player2_id,
            winner_id,
            start_datetime,
            DATE_ADD(start_datetime, INTERVAL match_duration MINUTE),
            match_duration,
            game_moves,
            -- Hits and misses only for Battleship
            CASE WHEN current_game_name = 'Battleship'
                THEN FLOOR(RAND() * 17) ELSE 0 END,
            CASE WHEN current_game_name = 'Battleship'
                THEN FLOOR(RAND() * 40) ELSE 0 END,
            CASE WHEN current_game_name = 'Battleship'
                THEN FLOOR(RAND() * 17) ELSE 0 END,
            CASE WHEN current_game_name = 'Battleship'
                THEN FLOOR(RAND() * 40) ELSE 0 END,
            JSON_OBJECT(
                'final_state', 'completed',
                'last_move', CONCAT('move_', game_moves)
            ),
            game_outcome
        );

        SET i = i + 1;
    END WHILE;
END //

DELIMITER ;

-- Execute the procedure
CALL generate_matches();

-- Clean up
DROP PROCEDURE IF EXISTS generate_matches;
DROP TEMPORARY TABLE IF EXISTS temp_game_ids;
DROP TEMPORARY TABLE IF EXISTS temp_player_ids;

# -------------------------------------------------------------------------------------------------------------------------------------------------------------

DELIMITER //

CREATE PROCEDURE generate_player_game_stats()
BEGIN
    -- Create temporary table to store the latest match dates per player and game
    CREATE TEMPORARY TABLE temp_last_played AS
    SELECT
        COALESCE(player1_id, player2_id) as player_id,
        game_id,
        MAX(end_time) as last_played
    FROM matches
    WHERE end_time IS NOT NULL
    GROUP BY COALESCE(player1_id, player2_id), game_id;

    -- Insert player game statistics
    INSERT INTO player_game_stats (
        stat_id, player_id, game_id, total_games_played,
        result, total_moves, total_hits, total_misses,
        total_time_played_minutes, highest_score, win_ratio,
        rating, churned, player_level, last_played
    )
    WITH player_game_metrics AS (
        SELECT
            p.player_id,
            m.game_id,
            COUNT(m.match_id) as games_played,
            -- Calculate wins
            COUNT(CASE WHEN m.winner_id = p.player_id THEN 1 END) as wins,
            -- Calculate most common result
            (
                SELECT result
                FROM (
                    SELECT
                        CASE
                            WHEN m2.winner_id = p.player_id THEN 'WIN'
                            WHEN m2.winner_id IS NULL AND m2.game_result = 'DRAW' THEN 'DRAW'
                            WHEN m2.game_result = 'ABANDONED' THEN 'ABANDONED'
                            ELSE 'LOSS'
                        END as result,
                        COUNT(*) as cnt
                    FROM matches m2
                    WHERE (m2.player1_id = p.player_id OR m2.player2_id = p.player_id)
                    AND m2.game_id = m.game_id
                    GROUP BY result
                    ORDER BY cnt DESC
                    LIMIT 1
                ) t
            ) as most_common_result,
            -- Sum all moves
            SUM(moves_count) as total_moves,
            -- Sum hits and misses (for Battleship)
            SUM(CASE WHEN m.player1_id = p.player_id THEN player1_hits ELSE player2_hits END) as total_hits,
            SUM(CASE WHEN m.player1_id = p.player_id THEN player1_misses ELSE player2_misses END) as total_misses,
            -- Calculate total time played
            SUM(duration_minutes) as total_time,
            -- Get maximum score (using moves_count as a proxy for score)
            MAX(moves_count) as max_score,
            -- Calculate win ratio
            (COUNT(CASE WHEN m.winner_id = p.player_id THEN 1 END) * 100.0 /
                COUNT(CASE WHEN m.game_result != 'ABANDONED' THEN 1 END)) as win_percentage,
            -- Get last played date
            MAX(m.end_time) as last_game_date
        FROM
            players p
            CROSS JOIN games g
            LEFT JOIN matches m ON (m.player1_id = p.player_id OR m.player2_id = p.player_id)
                AND m.game_id = g.game_id
        GROUP BY
            p.player_id, m.game_id
        HAVING
            games_played > 0
    )
    SELECT
        UUID_TO_BIN(UUID()) as stat_id,
        pgm.player_id,
        pgm.game_id,
        pgm.games_played as total_games_played,
        pgm.most_common_result as result,
        pgm.total_moves,
        pgm.total_hits,
        pgm.total_misses,
        pgm.total_time as total_time_played_minutes,
        pgm.max_score as highest_score,
        pgm.win_percentage as win_ratio,
        -- Calculate rating based on win ratio and games played
        CASE
            WHEN pgm.win_percentage >= 70 AND pgm.games_played >= 20 THEN 5
            WHEN pgm.win_percentage >= 60 AND pgm.games_played >= 15 THEN 4
            WHEN pgm.win_percentage >= 50 AND pgm.games_played >= 10 THEN 3
            WHEN pgm.win_percentage >= 40 AND pgm.games_played >= 5 THEN 2
            ELSE 1
        END as rating,
        -- Determine churn status (if haven't played in last 60 days)
        CASE
            WHEN DATEDIFF(NOW(), pgm.last_game_date) > 60 THEN 'YES'
            ELSE 'NO'
        END as churned,
        -- Determine player level based on games played, win ratio, and time invested
        CASE
            WHEN pgm.games_played >= 30 AND pgm.win_percentage >= 70
                AND pgm.total_time >= 1000 THEN 'Expert'
            WHEN pgm.games_played >= 15 AND pgm.win_percentage >= 50
                AND pgm.total_time >= 500 THEN 'Intermediate'
            ELSE 'Novice'
        END as player_level,
        pgm.last_game_date as last_played
    FROM
        player_game_metrics pgm
    WHERE
        pgm.games_played > 0;

    -- Clean up
    DROP TEMPORARY TABLE IF EXISTS temp_last_played;
END //

DELIMITER ;

-- Execute the procedure
CALL generate_player_game_stats();

-- Clean up
DROP PROCEDURE IF EXISTS generate_player_game_stats;

