-- Insert game data
INSERT INTO games (game_id, name, description, rules, can_draw) VALUES
(UUID_TO_BIN(UUID()),
'battleship',
'Strategic naval combat game where players try to sink each other''s fleet',
'Players place ships on a grid and take turns calling out coordinates to find and sink opponent''s ships. First to sink all enemy ships wins.',
FALSE),

(UUID_TO_BIN(UUID()),
'chess',
'Classic strategy board game of kings and queens',
'Players move pieces according to specific rules with the goal of checkmating the opponent''s king. Each piece has unique movement patterns.',
TRUE),

(UUID_TO_BIN(UUID()),
'connect four',
'Vertical strategy game of aligning four tokens',
'Players take turns dropping colored tokens into a vertical grid. First to connect four tokens horizontally, vertically, or diagonally wins.',
TRUE),

(UUID_TO_BIN(UUID()),
'tic tac toe',
'Classic game of X''s and O''s',
'Players take turns marking spaces in a 3×3 grid. First player to align three of their marks horizontally, vertically, or diagonally wins.',
TRUE),

(UUID_TO_BIN(UUID()),
'dots and boxes',
'Strategic game of connecting dots to form boxes',
'Players take turns connecting adjacent dots. When a player completes a box, they claim it and get another turn. Player with most boxes wins.',
FALSE);

DELIMITER //

-- Procedure to generate players (unchanged as players table structure remains similar)
CREATE PROCEDURE generate_players()
BEGIN
    -- [Previous generate_players code remains the same]
END //

-- Updated procedure to generate matches with normalized structure
CREATE PROCEDURE generate_matches()
BEGIN
    DECLARE min_matches INT DEFAULT 9;
    DECLARE max_matches INT DEFAULT 200;
    DECLARE battleship_id BINARY(16);

    -- Get battleship game_id
    SELECT game_id INTO battleship_id FROM games WHERE name = 'battleship';

    -- Set date ranges avoiding DST transition dates
    SET @period1_start = '2024-01-01';
    SET @period1_end = '2024-03-30';
    SET @period2_start = '2024-04-01';
    SET @period2_end = '2024-12-13';

    BEGIN
        DECLARE done INT DEFAULT FALSE;
        DECLARE curr_player_id BINARY(16);
        DECLARE player_cursor CURSOR FOR SELECT player_id FROM players;
        DECLARE CONTINUE HANDLER FOR NOT FOUND SET done = TRUE;

        OPEN player_cursor;

        player_loop: LOOP
            FETCH player_cursor INTO curr_player_id;
            IF done THEN
                LEAVE player_loop;
            END IF;

            -- Determine which games this player will play (probabilities remain same)
            SET @plays_battleship = IF(RAND() < 0.8, 1, 0);
            SET @plays_chess = IF(RAND() < 0.6, 1, 0);
            SET @plays_connect_four = IF(RAND() < 0.5, 1, 0);
            SET @plays_tic_tac_toe = IF(RAND() < 0.7, 1, 0);
            SET @plays_dots_boxes = IF(RAND() < 0.5, 1, 0);

            -- Generate matches for each game type
            IF @plays_battleship = 1 THEN
                CALL generate_game_matches(curr_player_id, battleship_id, 15 + FLOOR(RAND() * 135));
            END IF;

            -- Generate matches for other games
            IF @plays_chess = 1 THEN
                CALL generate_game_matches(
                    curr_player_id,
                    (SELECT game_id FROM games WHERE name = 'chess'),
                    9 + FLOOR(RAND() * 41)
                );
            END IF;

            -- [Similar blocks for other games]
        END LOOP;

        CLOSE player_cursor;
    END;
END //

-- Updated procedure to generate matches for a specific game
CREATE PROCEDURE generate_game_matches(
    IN p_player_id BINARY(16),
    IN p_game_id BINARY(16),
    IN p_num_matches INT
)
BEGIN
    DECLARE i INT DEFAULT 0;
    DECLARE match_id BINARY(16);

    WHILE i < p_num_matches DO
        -- Select opponent
        SET @opponent_id = (
            SELECT player_id
            FROM players
            WHERE player_id != p_player_id
            ORDER BY RAND()
            LIMIT 1
        );

        -- Get game details
        SELECT can_draw INTO @can_draw
        FROM games
        WHERE game_id = p_game_id;

        -- Generate match duration and moves
        SET @duration = 10 + FLOOR(RAND() * 50);
        SET @p1_moves = 10 + FLOOR(RAND() * 40);
        SET @p2_moves = 10 + FLOOR(RAND() * 40);

        -- Determine result and winner
        IF @can_draw AND RAND() < 0.1 THEN
            SET @result = 'draw';
            SET @winner_id = NULL;
        ELSE
            IF RAND() < 0.5 THEN
                SET @result = 'win';
                SET @winner_id = p_player_id;
            ELSE
                SET @result = 'loss';
                SET @winner_id = @opponent_id;
            END IF;
        END IF;

        -- Generate random timestamp
        SET @start_time = TIMESTAMP(
            DATE_ADD('2024-01-01',
            INTERVAL FLOOR(RAND() * DATEDIFF('2024-12-13', '2024-01-01')) DAY)
        );
        SET @end_time = DATE_ADD(@start_time, INTERVAL @duration MINUTE);

        -- Insert match
        SET match_id = UUID_TO_BIN(UUID());

        INSERT INTO match_history (
            match_id, game_id, player1_id, player2_id,
            winner_id, start_time, end_time, duration_minutes, result
        )
        VALUES (
            match_id,
            p_game_id,
            p_player_id,
            @opponent_id,
            @winner_id,
            @start_time,
            @end_time,
            @duration,
            @result
        );

        -- Insert move records
        INSERT INTO match_moves (move_id, match_id, player_id, moves_count)
        VALUES
        (UUID_TO_BIN(UUID()), match_id, p_player_id, @p1_moves),
        (UUID_TO_BIN(UUID()), match_id, @opponent_id, @p2_moves);

        SET i = i + 1;
    END WHILE;
END //

-- Updated procedure to generate player game statistics
CREATE PROCEDURE generate_player_game_stats()
BEGIN
    -- Clear existing stats
    TRUNCATE TABLE player_game_stats;
    TRUNCATE TABLE player_ratings;

    -- Insert aggregated stats
    INSERT INTO player_game_stats (
        stat_id,
        player_id,
        game_id,
        total_games_played,
        total_wins,
        total_losses,
        total_draws,
        total_moves,
        total_time_played_minutes,
        last_played
    )
    SELECT
        UUID_TO_BIN(UUID()),
        p.player_id,
        g.game_id,
        COUNT(DISTINCT m.match_id) as total_games_played,
        SUM(CASE WHEN m.winner_id = p.player_id THEN 1 ELSE 0 END) as total_wins,
        SUM(CASE WHEN m.winner_id IS NOT NULL AND m.winner_id != p.player_id THEN 1 ELSE 0 END) as total_losses,
        SUM(CASE WHEN m.winner_id IS NULL THEN 1 ELSE 0 END) as total_draws,
        SUM(mm.moves_count) as total_moves,
        SUM(m.duration_minutes) as total_time_played_minutes,
        MAX(m.end_time) as last_played
    FROM
        players p
        INNER JOIN match_history m ON (m.player1_id = p.player_id OR m.player2_id = p.player_id)
        INNER JOIN games g ON m.game_id = g.game_id
        INNER JOIN match_moves mm ON mm.match_id = m.match_id AND mm.player_id = p.player_id
    GROUP BY
        p.player_id,
        g.game_id
    HAVING
        COUNT(DISTINCT m.match_id) > 0;

    -- Insert ratings
    INSERT INTO player_ratings (
        rating_id,
        player_id,
        game_id,
        rating,
        rating_date
    )
    SELECT
        UUID_TO_BIN(UUID()),
        s.player_id,
        s.game_id,
        CASE
            WHEN s.total_games_played < 5 THEN 1  -- New players
            ELSE
                GREATEST(1, LEAST(5,  -- Ensure rating is between 1 and 5
                    FLOOR(
                        (
                            -- Win ratio contribution (50% weight)
                            (s.total_wins * 100.0 / s.total_games_played * 0.5) +
                            -- Games played contribution (30% weight)
                            (CASE
                                WHEN s.total_games_played >= 50 THEN 100
                                ELSE s.total_games_played * 2
                             END * 0.3) +
                            -- Time played contribution (20% weight)
                            (CASE
                                WHEN s.total_time_played_minutes >= 1000 THEN 100
                                ELSE s.total_time_played_minutes / 10
                             END * 0.2)
                        ) / 20  -- Divide by 20 to get a 1-5 scale
                    )
                ))
        END as rating,
        CURRENT_TIMESTAMP
    FROM player_game_stats s;
END //

DELIMITER ;

-- Generate the data
CALL generate_players();
CALL generate_matches();
CALL generate_player_game_stats();

-- Clean up procedures
DROP PROCEDURE IF EXISTS generate_players;
DROP PROCEDURE IF EXISTS generate_matches;
DROP PROCEDURE IF EXISTS generate_game_matches;
DROP PROCEDURE IF EXISTS generate_player_game_stats;