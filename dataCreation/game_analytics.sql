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

# # -- Achievements table
# # CREATE TABLE achievements (
# #     achievement_id BINARY(16) PRIMARY KEY,
# #     game_id BINARY(16),
# #     achievement_name VARCHAR(100) NOT NULL,
# #     game_name VARCHAR(100) NOT NULL,
# #     description TEXT,
# #     criteria TEXT,
# #     points INT DEFAULT 0,
# #     FOREIGN KEY (game_id) REFERENCES games(game_id)
# # );
# #
# # -- Player Achievements
# # CREATE TABLE player_achievements (
# #     player_id BINARY(16),
# #     achievement_id BINARY(16),
# #     unlocked_at TIMESTAMP,
# #     PRIMARY KEY (player_id, achievement_id),
# #     FOREIGN KEY (player_id) REFERENCES players(player_id),
# #     FOREIGN KEY (achievement_id) REFERENCES achievements(achievement_id)
# # );
# #
# # -- Friends system
# # CREATE TABLE friendships (
# #     friendship_id BINARY(16) PRIMARY KEY,
# #     requester_id BINARY(16),
# #     addressee_id BINARY(16),
# #     status ENUM('PENDING', 'ACCEPTED', 'REJECTED', 'BLOCKED') DEFAULT 'PENDING',
# #     created_at TIMESTAMP,
# #     updated_at TIMESTAMP,
# #     FOREIGN KEY (requester_id) REFERENCES players(player_id),
# #     FOREIGN KEY (addressee_id) REFERENCES players(player_id),
# #     UNIQUE KEY unique_friendship (requester_id, addressee_id)
# # );
#
#
# -- Indexes for better query performance
# CREATE INDEX idx_matches_game_id ON matches(game_id);
# CREATE INDEX idx_matches_players ON matches(player1_id, player2_id);
# CREATE INDEX idx_player_stats_game ON player_game_stats(game_id);
# CREATE INDEX idx_player_stats_player ON player_game_stats(player_id);
# # CREATE INDEX idx_achievements_game ON achievements(game_id);
# # CREATE INDEX idx_friendships_players ON friendships(requester_id, addressee_id);
# # CREATE INDEX idx_player_game_rating ON player_game_stats(game_id, rating DESC);
#
#
#
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


DROP TRIGGER IF EXISTS player_game_stats_after_insert;
DROP TRIGGER IF EXISTS player_game_stats_after_update;
DROP TRIGGER IF EXISTS player_game_stats_after_delete;
DROP TABLE IF EXISTS player_game_stats_audit;

# Audit table for player_game_stats
CREATE TABLE player_game_stats_audit (
    audit_id BINARY(16) PRIMARY KEY,
    stat_id BINARY(16),
    player_id BINARY(16),
    game_id BINARY(16),
    action_type ENUM('INSERT', 'UPDATE', 'DELETE') NOT NULL,
    total_games_played INT,
    result ENUM('WIN', 'LOSS', 'DRAW', 'ABANDONED'),
    total_moves INT,
    total_hits INT,           -- Changed from hits to total_hits
    total_misses INT,         -- Changed from misses to total_misses
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

-- Create UPDATE trigger
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


-- Create DELETE trigger
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

#--------------------------------------------------------------------------------------------------------------------------------------------------------------------

DELIMITER //

-- Player Generation (500 players)
CREATE PROCEDURE generate_players()
BEGIN
   DECLARE i INT DEFAULT 0;
   DECLARE username_suffix VARCHAR(10);
   DECLARE email_suffix VARCHAR(10);
   DECLARE email_domain VARCHAR(100);
   DECLARE random_age INT;
   DECLARE random_gender VARCHAR(20);
   DECLARE random_country VARCHAR(100);

   WHILE i < 500 DO
       SET username_suffix = LPAD(i, 5, '0');
       SET email_suffix = LPAD(i, 5, '0');
       SET email_domain = ELT(FLOOR(1 + RAND() * 5),
           '@gmail.com', '@yahoo.com', '@hotmail.com', '@outlook.com', '@icloud.com');
       SET random_age = FLOOR(13 + RAND() * 67);
       SET random_gender = ELT(FLOOR(1 + RAND() * 4),
           'MALE', 'FEMALE', 'NON-BINARY', 'OTHER');
       SET random_country = ELT(FLOOR(1 + RAND() * 30),
           'USA', 'Canada', 'UK', 'Australia', 'Germany', 'France', 'Spain',
           'Italy', 'Japan', 'South Korea', 'Brazil', 'Mexico', 'India',
           'Russia', 'China', 'Netherlands', 'Sweden', 'Norway', 'Denmark',
           'Finland', 'Ireland', 'New Zealand', 'Singapore', 'Malaysia',
           'Philippines', 'Thailand', 'Vietnam', 'Indonesia', 'South Africa', 'Nigeria');

       CASE FLOOR(1 + RAND() * 4)
           WHEN 1 THEN
               INSERT INTO players (player_id, username, email, age, gender, country, last_login)
               VALUES (
                   UUID_TO_BIN(UUID()),
                   CONCAT(
                       ELT(FLOOR(1 + RAND() * 5), 'Pro', 'Elite', 'Epic', 'Master', 'Ultra'),
                       ELT(FLOOR(1 + RAND() * 5), 'Gamer', 'Player', 'Champion', 'Warrior', 'Legend'),
                       '_', username_suffix
                   ),
                   CONCAT('player', email_suffix, email_domain),
                   random_age,
                   random_gender,
                   random_country,
                   DATE_SUB(NOW(), INTERVAL FLOOR(RAND() * 30) DAY)
               );
           WHEN 2 THEN
               INSERT INTO players (player_id, username, email, age, gender, country, last_login)
               VALUES (
                   UUID_TO_BIN(UUID()),
                   CONCAT(
                       ELT(FLOOR(1 + RAND() * 5), 'Night', 'Dark', 'Storm', 'Fire', 'Ice'),
                       ELT(FLOOR(1 + RAND() * 5), 'Wolf', 'Dragon', 'Phoenix', 'Hawk', 'Knight'),
                       username_suffix
                   ),
                   CONCAT('gamer', email_suffix, email_domain),
                   random_age,
                   random_gender,
                   random_country,
                   DATE_SUB(NOW(), INTERVAL FLOOR(RAND() * 30) DAY)
               );
           WHEN 3 THEN
               INSERT INTO players (player_id, username, email, age, gender, country, last_login)
               VALUES (
                   UUID_TO_BIN(UUID()),
                   CONCAT(
                       ELT(FLOOR(1 + RAND() * 8), 'Chess', 'Battle', 'Dots', 'Connect', 'Memory', 'Tic', 'Box', 'Game'),
                       ELT(FLOOR(1 + RAND() * 5), 'Master', 'King', 'Queen', 'Lord', 'Boss'),
                       username_suffix
                   ),
                   CONCAT('gaming', email_suffix, email_domain),
                   random_age,
                   random_gender,
                   random_country,
                   DATE_SUB(NOW(), INTERVAL FLOOR(RAND() * 30) DAY)
               );
           ELSE
               INSERT INTO players (player_id, username, email, age, gender, country, last_login)
               VALUES (
                   UUID_TO_BIN(UUID()),
                   CONCAT(
                       ELT(FLOOR(1 + RAND() * 5), 'Player', 'Gamer', 'User', 'Challenger', 'Champion'),
                       username_suffix
                   ),
                   CONCAT('user', email_suffix, email_domain),
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

CALL generate_players();
DROP PROCEDURE IF EXISTS generate_players;

#-------------------------------------------------------------------------------------------------------------------------------------------

-- Match Generation (targeting 10000+ matches)

DELIMITER //

CREATE PROCEDURE generate_matches()
BEGIN
    CREATE TEMPORARY TABLE temp_player_game_prefs (
        id INT AUTO_INCREMENT PRIMARY KEY,
        player_id BINARY(16),
        game_id BINARY(16),
        game_name VARCHAR(100),
        target_games INT DEFAULT 0,
        games_played INT DEFAULT 0
    );

    -- Populate preferences
    INSERT INTO temp_player_game_prefs (player_id, game_id, game_name, target_games)
    SELECT
        p.player_id,
        g.game_id,
        g.name,
        CASE
            WHEN g.name = 'Battleship' THEN
                CASE
                    WHEN RAND() < 0.3 THEN 30 + FLOOR(RAND() * 21)
                    WHEN RAND() < 0.5 THEN 20 + FLOOR(RAND() * 11)
                    ELSE 10 + FLOOR(RAND() * 11)
                END
            WHEN RAND() < 0.6 THEN
                CASE g.name
                    WHEN 'Chess' THEN 15 + FLOOR(RAND() * 16)
                    WHEN 'Checkers' THEN 12 + FLOOR(RAND() * 14)
                    ELSE 8 + FLOOR(RAND() * 13)
                END
            ELSE 0
        END
    FROM players p
    CROSS JOIN games g;

    -- Match generation loop
    WHILE (SELECT COUNT(*) FROM matches) < 10000 DO
        SET @player1_id = NULL;
        SET @player2_id = NULL;
        SET @game_id = NULL;
        SET @game_name = NULL;

        -- Select first player and game
        SELECT player_id, game_id, game_name
        INTO @player1_id, @game_id, @game_name
        FROM temp_player_game_prefs
        WHERE games_played < target_games
        ORDER BY RAND() LIMIT 1;

        -- Select second player
        SELECT player_id INTO @player2_id
        FROM temp_player_game_prefs
        WHERE game_id = @game_id
        AND player_id != @player1_id
        AND games_played < target_games
        ORDER BY RAND() LIMIT 1;

        -- Insert match if both players found
        IF @player1_id IS NOT NULL AND @player2_id IS NOT NULL THEN
            INSERT INTO matches (
                match_id, game_id, player1_id, player2_id, winner_id,
                start_time, end_time, duration_minutes, moves_count,
                player1_hits, player1_misses, player2_hits, player2_misses,
                game_state, game_result
            )
            VALUES (
                UUID_TO_BIN(UUID()),
                @game_id,
                @player1_id,
                @player2_id,
                IF(RAND() < 0.2, NULL, IF(RAND() < 0.5, @player1_id, @player2_id)),
                DATE_SUB(NOW(), INTERVAL FLOOR(RAND() * (2 * 365)) DAY),
                NULL,
                CASE @game_name
                    WHEN 'Battleship' THEN 15 + FLOOR(RAND() * 30)
                    WHEN 'Chess' THEN 20 + FLOOR(RAND() * 40)
                    WHEN 'Checkers' THEN 10 + FLOOR(RAND() * 20)
                    WHEN 'Connect Four' THEN 5 + FLOOR(RAND() * 10)
                    WHEN 'Memory Match' THEN 5 + FLOOR(RAND() * 15)
                    WHEN 'Tic Tac Toe' THEN 2 + FLOOR(RAND() * 5)
                    WHEN 'Dots and Boxes' THEN 10 + FLOOR(RAND() * 20)
                    ELSE 10 + FLOOR(RAND() * 20)
                END,
                CASE @game_name
                    WHEN 'Battleship' THEN 35 + FLOOR(RAND() * 45)
                    WHEN 'Chess' THEN 30 + FLOOR(RAND() * 40)
                    ELSE 15 + FLOOR(RAND() * 25)
                END,
                IF(@game_name = 'Battleship', FLOOR(RAND() * 17), 0),
                IF(@game_name = 'Battleship', FLOOR(RAND() * 40), 0),
                IF(@game_name = 'Battleship', FLOOR(RAND() * 17), 0),
                IF(@game_name = 'Battleship', FLOOR(RAND() * 40), 0),
                JSON_OBJECT('final_state', 'completed'),
                CASE
                    WHEN RAND() < 0.2 THEN 'ABANDONED'
                    WHEN RAND() < 0.1 AND @game_name IN ('Chess', 'Tic Tac Toe', 'Connect Four') THEN 'DRAW'
                    ELSE 'WIN'
                END
            );

            -- Update end_time
            UPDATE matches
            SET end_time = DATE_ADD(start_time, INTERVAL duration_minutes MINUTE)
            WHERE end_time IS NULL;

            -- Update games played
            UPDATE temp_player_game_prefs
            SET games_played = games_played + 1
            WHERE player_id IN (@player1_id, @player2_id)
            AND game_id = @game_id;
        END IF;
    END WHILE;

    DROP TEMPORARY TABLE IF EXISTS temp_player_game_prefs;
END //

DELIMITER ;

CALL generate_matches();
DROP PROCEDURE IF EXISTS generate_matches;

# -------------------------------------------------------------------------------------------------------------------------------------------------------------

-- Create player_game_stats

DELIMITER //

CREATE PROCEDURE generate_player_game_stats()
BEGIN
    INSERT INTO player_game_stats (
        stat_id, player_id, game_id, total_games_played,
        result, total_moves, total_hits, total_misses,
        total_time_played_minutes, highest_score, win_ratio,
        rating, churned, player_level, last_played
    )
    SELECT
        UUID_TO_BIN(UUID()),
        player_id,
        game_id,
        games_played,
        result,
        moves,
        hits,
        misses,
        play_time,
        score,
        win_pct,
        rating,
        churn_status,
        level,
        last_game
    FROM (
        SELECT
            p.player_id,
            g.game_id,
            COUNT(m.match_id) as games_played,
            CASE
                WHEN SUM(CASE WHEN m.winner_id = p.player_id THEN 1 END) > SUM(CASE WHEN m.winner_id != p.player_id AND m.winner_id IS NOT NULL THEN 1 END) THEN 'WIN'
                WHEN SUM(CASE WHEN m.game_result = 'ABANDONED' THEN 1 END) > SUM(CASE WHEN m.game_result != 'ABANDONED' THEN 1 END) THEN 'ABANDONED'
                WHEN SUM(CASE WHEN m.game_result = 'DRAW' THEN 1 END) > SUM(CASE WHEN m.game_result != 'DRAW' THEN 1 END) THEN 'DRAW'
                ELSE 'LOSS'
            END as result,
            SUM(moves_count) as moves,
            SUM(CASE WHEN m.player1_id = p.player_id THEN m.player1_hits ELSE m.player2_hits END) as hits,
            SUM(CASE WHEN m.player1_id = p.player_id THEN m.player1_misses ELSE m.player2_misses END) as misses,
            SUM(duration_minutes) as play_time,
            MAX(moves_count) as score,
            (COUNT(CASE WHEN m.winner_id = p.player_id THEN 1 END) * 100.0 /
                NULLIF(COUNT(CASE WHEN m.game_result != 'ABANDONED' AND m.end_time IS NOT NULL THEN 1 END), 0)) as win_pct,
            CASE
                WHEN (COUNT(CASE WHEN m.winner_id = p.player_id THEN 1 END) * 100.0 /
                    NULLIF(COUNT(CASE WHEN m.game_result != 'ABANDONED' AND m.end_time IS NOT NULL THEN 1 END), 0)) >= 60
                    AND COUNT(m.match_id) >= 20 THEN 5
                WHEN (COUNT(CASE WHEN m.winner_id = p.player_id THEN 1 END) * 100.0 /
                    NULLIF(COUNT(CASE WHEN m.game_result != 'ABANDONED' AND m.end_time IS NOT NULL THEN 1 END), 0)) >= 50
                    AND COUNT(m.match_id) >= 15 THEN 4
                WHEN (COUNT(CASE WHEN m.winner_id = p.player_id THEN 1 END) * 100.0 /
                    NULLIF(COUNT(CASE WHEN m.game_result != 'ABANDONED' AND m.end_time IS NOT NULL THEN 1 END), 0)) >= 40
                    AND COUNT(m.match_id) >= 10 THEN 3
                WHEN (COUNT(CASE WHEN m.winner_id = p.player_id THEN 1 END) * 100.0 /
                    NULLIF(COUNT(CASE WHEN m.game_result != 'ABANDONED' AND m.end_time IS NOT NULL THEN 1 END), 0)) >= 25
                    AND COUNT(m.match_id) >= 5 THEN 2
                ELSE 1
            END as rating,
            CASE
                WHEN (SELECT COUNT(*)
                      FROM matches m2
                      WHERE (m2.player1_id = p.player_id OR m2.player2_id = p.player_id)
                      AND m2.end_time >= DATE_SUB(NOW(), INTERVAL 30 DAY)) < 3
                THEN 'YES'
                ELSE 'NO'
            END as churn_status,
            CASE
                WHEN COUNT(m.match_id) >= 10 AND
                     ((COUNT(CASE WHEN m.winner_id = p.player_id THEN 1 END) * 100.0 /
                     NULLIF(COUNT(CASE WHEN m.game_result != 'ABANDONED' AND m.end_time IS NOT NULL THEN 1 END), 0)) >= 50 OR  -- Reduced from 60
                     SUM(CASE WHEN m.player1_id = p.player_id THEN m.player1_hits ELSE m.player2_hits END) >= 100) AND  -- Added hits criteria
                     SUM(duration_minutes) >= 300 THEN 'Expert'
                WHEN COUNT(m.match_id) >= 8 AND
                    ((COUNT(CASE WHEN m.winner_id = p.player_id THEN 1 END) * 100.0 /
                     NULLIF(COUNT(CASE WHEN m.game_result != 'ABANDONED' AND m.end_time IS NOT NULL THEN 1 END), 0)) >= 35 OR  -- Reduced from 45
                     SUM(CASE WHEN m.player1_id = p.player_id THEN m.player1_hits ELSE m.player2_hits END) >= 50) AND   -- Added hits criteria
                     SUM(duration_minutes) >= 150 THEN 'Intermediate'
                ELSE 'Novice'
            END as level,
            MAX(CASE WHEN m.end_time IS NOT NULL THEN m.end_time ELSE NOW() END) as last_game
        FROM
            players p
            CROSS JOIN games g
            INNER JOIN matches m ON (m.player1_id = p.player_id OR m.player2_id = p.player_id)
                AND m.game_id = g.game_id
        WHERE m.end_time IS NOT NULL
        GROUP BY
            p.player_id, g.game_id
        HAVING
            COUNT(m.match_id) > 0
    ) stats;
END //

DELIMITER ;

CALL generate_player_game_stats();
DROP PROCEDURE IF EXISTS generate_player_game_stats;

#
# DESCRIBE player_game_stats;
#
# SELECT COLUMN_NAME
# FROM INFORMATION_SCHEMA.COLUMNS
# WHERE TABLE_SCHEMA = 'game_analytics'
# AND TABLE_NAME = 'player_game_stats'
# ORDER BY ORDINAL_POSITION;
#
#
#
#
# INSERT INTO player_game_stats (
#     stat_id,
#     player_id,
#     game_id,
#     total_games_played
# )
# SELECT
#     UUID_TO_BIN(UUID()),
#     p.player_id,
#     g.game_id,
#     COUNT(m.match_id) as total_games_played
# FROM
#     players p
#     CROSS JOIN games g
#     INNER JOIN matches m ON (m.player1_id = p.player_id OR m.player2_id = p.player_id)
#         AND m.game_id = g.game_id
# WHERE m.end_time IS NOT NULL
# GROUP BY
#     p.player_id, g.game_id
# LIMIT 1;
#
# DESCRIBE player_game_stats_audit;