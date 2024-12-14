# --------------------------------------------------------------------------------------------------------------------------------
# --------------------------------------------------------------------------------------------------------------------------------



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

-- Procedure to generate players
CREATE PROCEDURE generate_players()
BEGIN
    DECLARE i INT DEFAULT 0;
    DECLARE first_name VARCHAR(50);
    DECLARE last_name VARCHAR(50);
    DECLARE username_suffix VARCHAR(10);

    -- Define arrays of names
    DECLARE first_names VARCHAR(1000) DEFAULT 'James,John,Robert,Michael,William,David,Joseph,Charles,Thomas,Daniel,Matthew,Anthony,Emma,Olivia,Ava,Isabella,Sophia,Mia,Charlotte,Amelia,Harper,Evelyn,Abigail,Emily';
    DECLARE last_names VARCHAR(1000) DEFAULT 'Smith,Johnson,Williams,Brown,Jones,Garcia,Miller,Davis,Rodriguez,Martinez,Hernandez,Lopez,Gonzales,Wilson,Anderson,Thomas,Taylor,Moore,Jackson,Martin';

    WHILE i < 200 DO
        -- Select random first and last names
        SET first_name = SUBSTRING_INDEX(SUBSTRING_INDEX(first_names, ',', 1 + FLOOR(1 + RAND() * 24)), ',', -1);
        SET last_name = SUBSTRING_INDEX(SUBSTRING_INDEX(last_names, ',', 1 + FLOOR(1 + RAND() * 20)), ',', -1);

        -- Generate birthdate
        SET @birthdate = DATE_SUB(CURDATE(), INTERVAL 18 + FLOOR(RAND() * 40) YEAR);

        -- Create unique username with better randomization
        SET username_suffix = LPAD(FLOOR(RAND() * 99999), 5, '0');
        SET @username = CONCAT(
            LOWER(first_name),
            CASE FLOOR(RAND() * 3)
                WHEN 0 THEN '_'
                WHEN 1 THEN '.'
                ELSE ''
            END,
            CASE FLOOR(RAND() * 3)
                WHEN 0 THEN LOWER(last_name)
                WHEN 1 THEN LEFT(LOWER(last_name), 1)
                ELSE ''
            END,
            username_suffix
        );

        -- Create unique email
        SET @email = CONCAT(
            LOWER(first_name),
            CASE FLOOR(RAND() * 3)
                WHEN 0 THEN '.'
                WHEN 1 THEN '_'
                ELSE ''
            END,
            LOWER(last_name),
            username_suffix,
            '@',
            CASE FLOOR(1 + RAND() * 5)
                WHEN 1 THEN 'gmail.com'
                WHEN 2 THEN 'yahoo.com'
                WHEN 3 THEN 'hotmail.com'
                WHEN 4 THEN 'outlook.com'
                ELSE 'icloud.com'
            END
        );

        -- Insert player with guaranteed non-NULL values
        INSERT INTO players (
            player_id,
            username,
            firstname,
            lastname,
            email,
            birthdate,
            gender,
            country
        )
        VALUES (
            UUID_TO_BIN(UUID()),
            @username,
            first_name,
            last_name,
            @email,
            @birthdate,
            CASE FLOOR(1 + RAND() * 3)
                WHEN 1 THEN 'Male'
                WHEN 2 THEN 'Female'
                ELSE 'Non-Binary'
            END,
            CASE FLOOR(1 + RAND() * 10)
                WHEN 1 THEN 'USA'
                WHEN 2 THEN 'UK'
                WHEN 3 THEN 'Canada'
                WHEN 4 THEN 'Australia'
                WHEN 5 THEN 'Germany'
                WHEN 6 THEN 'France'
                WHEN 7 THEN 'Spain'
                WHEN 8 THEN 'Italy'
                WHEN 9 THEN 'Japan'
                ELSE 'Brazil'
            END
        );

        SET i = i + 1;
    END WHILE;
END //

-- Procedure to generate matches

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

            -- Determine which games this player will play
            -- 80% chance to play battleship
            SET @plays_battleship = IF(RAND() < 0.8, 1, 0);

            -- 50-70% chance to play each other game
            SET @plays_chess = IF(RAND() < 0.6, 1, 0);
            SET @plays_connect_four = IF(RAND() < 0.5, 1, 0);
            SET @plays_tic_tac_toe = IF(RAND() < 0.7, 1, 0);
            SET @plays_dots_boxes = IF(RAND() < 0.5, 1, 0);

            -- For each game the player plays, generate matches
            IF @plays_battleship = 1 THEN
                -- Generate more matches for battleship (15-150 matches)
                SET @player_matches = 15 + FLOOR(RAND() * 135);

                CALL generate_game_matches(
                    curr_player_id,
                    battleship_id,
                    @player_matches,
                    @period1_start,
                    @period1_end,
                    @period2_start,
                    @period2_end
                );
            END IF;

            -- Generate matches for other games if player plays them
            -- Chess
            IF @plays_chess = 1 THEN
                SET @player_matches = 9 + FLOOR(RAND() * 41); -- 9-50 matches

                CALL generate_game_matches(
                    curr_player_id,
                    (SELECT game_id FROM games WHERE name = 'chess'),
                    @player_matches,
                    @period1_start,
                    @period1_end,
                    @period2_start,
                    @period2_end
                );
            END IF;

            -- Connect Four
            IF @plays_connect_four = 1 THEN
                SET @player_matches = 9 + FLOOR(RAND() * 31); -- 9-40 matches

                CALL generate_game_matches(
                    curr_player_id,
                    (SELECT game_id FROM games WHERE name = 'connect four'),
                    @player_matches,
                    @period1_start,
                    @period1_end,
                    @period2_start,
                    @period2_end
                );
            END IF;

            -- Tic Tac Toe
            IF @plays_tic_tac_toe = 1 THEN
                SET @player_matches = 9 + FLOOR(RAND() * 21); -- 9-30 matches

                CALL generate_game_matches(
                    curr_player_id,
                    (SELECT game_id FROM games WHERE name = 'tic tac toe'),
                    @player_matches,
                    @period1_start,
                    @period1_end,
                    @period2_start,
                    @period2_end
                );
            END IF;

            -- Dots and Boxes
            IF @plays_dots_boxes = 1 THEN
                SET @player_matches = 9 + FLOOR(RAND() * 21); -- 9-30 matches

                CALL generate_game_matches(
                    curr_player_id,
                    (SELECT game_id FROM games WHERE name = 'dots and boxes'),
                    @player_matches,
                    @period1_start,
                    @period1_end,
                    @period2_start,
                    @period2_end
                );
            END IF;

        END LOOP;

        CLOSE player_cursor;
    END;
END //

-- Helper procedure to generate matches for a specific game
CREATE PROCEDURE generate_game_matches(
    IN p_player_id BINARY(16),
    IN p_game_id BINARY(16),
    IN p_num_matches INT,
    IN p_period1_start DATE,
    IN p_period1_end DATE,
    IN p_period2_start DATE,
    IN p_period2_end DATE
)
BEGIN
    DECLARE i INT DEFAULT 0;

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
        SELECT name, can_draw INTO @game_name, @can_draw
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

        -- Choose which period to use
        IF RAND() < 0.5 THEN
            SET @min_date = p_period1_start;
            SET @max_date = p_period1_end;
        ELSE
            SET @min_date = p_period2_start;
            SET @max_date = p_period2_end;
        END IF;

        -- Generate random date components
        SET @days_diff = DATEDIFF(@max_date, @min_date);
        SET @random_days = FLOOR(RAND() * @days_diff);
        SET @random_hour = LPAD(FLOOR(RAND() * 24), 2, '0');
        SET @random_minute = LPAD(FLOOR(RAND() * 60), 2, '0');

        -- Create timestamps using string concatenation
        SET @start_time = CONCAT(
            DATE_ADD(@min_date, INTERVAL @random_days DAY),
            ' ',
            @random_hour,
            ':',
            @random_minute,
            ':00'
        );

        SET @end_time = DATE_ADD(@start_time, INTERVAL @duration MINUTE);

        -- Insert match
        INSERT INTO match_history (
            match_id, game_id, game_name, player1_id, player2_id,
            winner_id, start_time, end_time, duration_minutes,
            player1_moves, player2_moves, result
        )
        VALUES (
            UUID_TO_BIN(UUID()),
            p_game_id,
            @game_name,
            p_player_id,
            @opponent_id,
            @winner_id,
            @start_time,
            @end_time,
            @duration,
            @p1_moves,
            @p2_moves,
            @result
        );

        SET i = i + 1;
    END WHILE;
END //

-- Procedure to generate player game statistics
CREATE PROCEDURE generate_player_game_stats()
BEGIN
    INSERT INTO player_game_stats (
        stat_id,
        player_id,
        player_name,
        age,
        gender,
        country,
        game_id,
        game_name,
        total_games_played,
        total_wins,
        total_losses,
        total_moves,
        total_time_played_minutes,
        result
    )
    SELECT
        UUID_TO_BIN(UUID()),
        p.player_id,
        CONCAT(p.firstname, ' ', p.lastname),
        TIMESTAMPDIFF(YEAR, p.birthdate, CURDATE()),
        p.gender,
        p.country,
        g.game_id,
        g.name,
        COUNT(DISTINCT m.match_id) as total_games_played,
        SUM(CASE WHEN m.winner_id = p.player_id THEN 1 ELSE 0 END) as total_wins,
        SUM(CASE WHEN m.winner_id IS NOT NULL AND m.winner_id != p.player_id THEN 1 ELSE 0 END) as total_losses,
        SUM(CASE WHEN m.player1_id = p.player_id THEN m.player1_moves ELSE m.player2_moves END) as total_moves,
        SUM(m.duration_minutes) as total_time_played_minutes,
        CASE
            WHEN COUNT(DISTINCT m.match_id) = 0 THEN NULL
            WHEN SUM(CASE WHEN m.winner_id = p.player_id THEN 1 ELSE 0 END) >
                 SUM(CASE WHEN m.winner_id IS NOT NULL AND m.winner_id != p.player_id THEN 1 ELSE 0 END)
            THEN 'win'
            WHEN SUM(CASE WHEN m.winner_id = p.player_id THEN 1 ELSE 0 END) <
                 SUM(CASE WHEN m.winner_id IS NOT NULL AND m.winner_id != p.player_id THEN 1 ELSE 0 END)
            THEN 'loss'
            ELSE 'draw'
        END as result
    FROM
        players p
        CROSS JOIN games g
        LEFT JOIN match_history m ON (m.player1_id = p.player_id OR m.player2_id = p.player_id)
            AND m.game_id = g.game_id
    GROUP BY
        p.player_id,
        CONCAT(p.firstname, ' ', p.lastname),
        TIMESTAMPDIFF(YEAR, p.birthdate, CURDATE()),
        p.gender,
        p.country,
        g.game_id,
        g.name;
END //

DELIMITER ;

-- Generate the data
CALL generate_players();
CALL generate_matches();
CALL generate_player_game_stats();

-- Clean up procedures
#
# DROP PROCEDURE IF EXISTS generate_players;
# DROP PROCEDURE IF EXISTS generate_matches;
# DROP PROCEDURE IF EXISTS generate_player_game_stats;
