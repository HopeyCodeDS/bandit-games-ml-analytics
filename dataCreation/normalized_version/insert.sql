-- Insert game data with two new games
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
FALSE),

(UUID_TO_BIN(UUID()),
'go',
'Ancient board game of territory control',
'Players place stones on intersections to capture territory and opponent''s stones. Player with most territory wins.',
FALSE),

(UUID_TO_BIN(UUID()),
'reversi',
'Strategic disk-flipping board game',
'Players place disks and flip opponent''s disks by trapping them between their own. Player with most disks wins.',
FALSE);

DELIMITER //

-- Procedure to generate diverse player base

CREATE PROCEDURE generate_players()
BEGIN
    DECLARE i INT DEFAULT 0;

    -- Arrays for diverse name generation
    DECLARE first_names VARCHAR(1000) DEFAULT 'James,John,Robert,Michael,William,David,Joseph,Emma,Olivia,Ava,Isabella,Sophia,Wei,Li,Zhang,Yuki,Haruto,Soma,Juan,Carlos,Maria,Sofia,Mohammed,Ahmad,Hassan,Amir,Zara,Priya,Raj,Arjun,Klaus,Hans,Anna,Elena,Ivan,Dmitri';
    DECLARE last_names VARCHAR(1000) DEFAULT 'Smith,Johnson,Williams,Brown,Garcia,Miller,Davis,Chen,Wang,Liu,Sato,Tanaka,Suzuki,Rodriguez,Martinez,Kumar,Patel,Singh,Mueller,Schmidt,Ivanov,Petrov,Kim,Lee,Park,Nguyen,Tran,Ali,Ahmed,Khan';

    WHILE i < 150 DO
        -- Select random first and last names for diversity
        SET @first_name = SUBSTRING_INDEX(SUBSTRING_INDEX(first_names, ',', 1 + FLOOR(1 + RAND() * 36)), ',', -1);
        SET @last_name = SUBSTRING_INDEX(SUBSTRING_INDEX(last_names, ',', 1 + FLOOR(1 + RAND() * 30)), ',', -1);

        -- Generate birthdate (18-65 years old)
        SET @birthdate = DATE_SUB(CURDATE(), INTERVAL 18 + FLOOR(RAND() * 47) YEAR);

        -- Create unique username with timestamp and random number
        SET @timestamp = DATE_FORMAT(NOW(6), '%y%m%d%H%i%s%f');
        SET @random_num = LPAD(FLOOR(RAND() * 1000), 3, '0');
        SET @username = CONCAT(
            LOWER(@first_name),
            CASE FLOOR(RAND() * 3)
                WHEN 0 THEN '_'
                WHEN 1 THEN '.'
                ELSE ''
            END,
            LOWER(@last_name),
            '_',
            @random_num,  -- Add random number
            SUBSTRING(@timestamp, -6)  -- Add last 6 digits of timestamp
        );

        -- Create unique email
        SET @email = CONCAT(
            LOWER(@first_name),
            '.',
            LOWER(@last_name),
            '_',
            @random_num,
            SUBSTRING(@timestamp, -4),
            '@',
            CASE FLOOR(1 + RAND() * 8)
                WHEN 1 THEN 'gmail.com'
                WHEN 2 THEN 'yahoo.com'
                WHEN 3 THEN 'hotmail.com'
                WHEN 4 THEN 'outlook.com'
                WHEN 5 THEN 'protonmail.com'
                WHEN 6 THEN 'mail.com'
                WHEN 7 THEN 'icloud.com'
                ELSE 'fastmail.com'
            END
        );

        -- Insert player with diverse demographics
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
            @first_name,
            @last_name,
            @email,
            @birthdate,
            CASE
                WHEN FLOOR(1 + RAND() * 100) = 1 THEN 'Non-Binary'  -- 1% Non-Binary
                WHEN FLOOR(1 + RAND() * 100) BETWEEN 2 AND 11 THEN 'Female'  -- 10% Female
                ELSE 'Male'  -- 89% Male (reflecting typical gaming demographics)
            END,
            CASE
                WHEN FLOOR(1 + RAND() * 100) BETWEEN 1 AND 15 THEN 'USA'  -- 15%
                WHEN FLOOR(1 + RAND() * 100) BETWEEN 16 AND 25 THEN 'China'  -- 10%
                WHEN FLOOR(1 + RAND() * 100) BETWEEN 26 AND 34 THEN 'Japan'  -- 9%
                WHEN FLOOR(1 + RAND() * 100) BETWEEN 35 AND 42 THEN 'Germany'  -- 8%
                WHEN FLOOR(1 + RAND() * 100) BETWEEN 43 AND 49 THEN 'UK'  -- 7%
                WHEN FLOOR(1 + RAND() * 100) BETWEEN 50 AND 56 THEN 'France'  -- 7%
                WHEN FLOOR(1 + RAND() * 100) BETWEEN 57 AND 63 THEN 'South Korea'  -- 7%
                WHEN FLOOR(1 + RAND() * 100) BETWEEN 64 AND 69 THEN 'Canada'  -- 6%
                WHEN FLOOR(1 + RAND() * 100) BETWEEN 70 AND 75 THEN 'India'  -- 6%
                WHEN FLOOR(1 + RAND() * 100) BETWEEN 76 AND 81 THEN 'Brazil'  -- 6%
                WHEN FLOOR(1 + RAND() * 100) BETWEEN 82 AND 86 THEN 'Russia'  -- 5%
                WHEN FLOOR(1 + RAND() * 100) BETWEEN 87 AND 91 THEN 'Spain'  -- 5%
                WHEN FLOOR(1 + RAND() * 100) BETWEEN 92 AND 95 THEN 'Australia'  -- 4%
                WHEN FLOOR(1 + RAND() * 100) BETWEEN 96 AND 98 THEN 'Netherlands'  -- 3%
                WHEN FLOOR(1 + RAND() * 100) = 99 THEN 'Sweden'  -- 1%
                ELSE 'Singapore'  -- 1%
            END
        );

        SET i = i + 1;
    END WHILE;
END //

-- Procedure to generate realistic match data
CREATE PROCEDURE generate_matches()
BEGIN
    DECLARE done INT DEFAULT FALSE;
    DECLARE curr_player_id BINARY(16);
    DECLARE player_cursor CURSOR FOR SELECT player_id FROM players;
    DECLARE CONTINUE HANDLER FOR NOT FOUND SET done = TRUE;

    -- Get game IDs
    SELECT game_id INTO @battleship_id FROM games WHERE name = 'battleship';
    SELECT game_id INTO @chess_id FROM games WHERE name = 'chess';
    SELECT game_id INTO @connect_four_id FROM games WHERE name = 'connect four';
    SELECT game_id INTO @tic_tac_toe_id FROM games WHERE name = 'tic tac toe';
    SELECT game_id INTO @dots_boxes_id FROM games WHERE name = 'dots and boxes';
    SELECT game_id INTO @go_id FROM games WHERE name = 'go';
    SELECT game_id INTO @reversi_id FROM games WHERE name = 'reversi';

    -- Set date range
    SET @min_date = '2023-01-01';
    SET @max_date = CURDATE();

    OPEN player_cursor;
    player_loop: LOOP
        FETCH player_cursor INTO curr_player_id;
        IF done THEN
            LEAVE player_loop;
        END IF;

        -- Assign game preferences (adjusted for more matches)
        SET @battleship_pref = RAND() * 100;
        SET @chess_pref = RAND() * 100;
        SET @connect_four_pref = RAND() * 100;
        SET @tic_tac_toe_pref = RAND() * 100;
        SET @dots_boxes_pref = RAND() * 100;
        SET @go_pref = RAND() * 100;
        SET @reversi_pref = RAND() * 100;

        -- Generate matches with increased numbers and lower thresholds
        IF @battleship_pref > 40 THEN  -- 60% chance
            CALL generate_game_matches(curr_player_id, @battleship_id, 30 + FLOOR(RAND() * 70));
        END IF;

        IF @chess_pref > 45 THEN  -- 55% chance
            CALL generate_game_matches(curr_player_id, @chess_id, 25 + FLOOR(RAND() * 55));
        END IF;

        IF @connect_four_pref > 50 THEN  -- 50% chance
            CALL generate_game_matches(curr_player_id, @connect_four_id, 20 + FLOOR(RAND() * 40));
        END IF;

        IF @tic_tac_toe_pref > 55 THEN  -- 45% chance
            CALL generate_game_matches(curr_player_id, @tic_tac_toe_id, 15 + FLOOR(RAND() * 35));
        END IF;

        IF @dots_boxes_pref > 60 THEN  -- 40% chance
            CALL generate_game_matches(curr_player_id, @dots_boxes_id, 10 + FLOOR(RAND() * 30));
        END IF;

        IF @go_pref > 70 THEN  -- 30% chance
            CALL generate_game_matches(curr_player_id, @go_id, 8 + FLOOR(RAND() * 22));
        END IF;

        IF @reversi_pref > 80 THEN  -- 20% chance
            CALL generate_game_matches(curr_player_id, @reversi_id, 5 + FLOOR(RAND() * 15));
        END IF;

    END LOOP;
    CLOSE player_cursor;
END //

-- Enhanced procedure to generate realistic matches
CREATE PROCEDURE generate_game_matches(
    IN p_player_id BINARY(16),
    IN p_game_id BINARY(16),
    IN p_num_matches INT
)
BEGIN
    DECLARE i INT DEFAULT 0;
    DECLARE match_id BINARY(16);

    -- Get player's skill level (persistent throughout matches)
    SET @player_skill = RAND();  -- 0 to 1 skill rating

    WHILE i < p_num_matches DO
        -- Select opponent with similar skill level (within ±0.3)
        SET @min_skill = GREATEST(0, @player_skill - 0.3);
        SET @max_skill = LEAST(1, @player_skill + 0.3);

        -- Select opponent
        SET @opponent_id = (
            SELECT player_id
            FROM players
            WHERE player_id != p_player_id
            ORDER BY RAND()
            LIMIT 1
        );

        -- Get game details
        SELECT can_draw INTO @can_draw FROM games WHERE game_id = p_game_id;

        -- Generate realistic match duration based on game type
        SET @base_duration = CASE
            WHEN p_game_id = @battleship_id THEN 15 + FLOOR(RAND() * 25)  -- 15-40 minutes
            WHEN p_game_id = @chess_id THEN 20 + FLOOR(RAND() * 40)       -- 20-60 minutes
            WHEN p_game_id = @go_id THEN 30 + FLOOR(RAND() * 60)          -- 30-90 minutes
            ELSE 5 + FLOOR(RAND() * 15)                                    -- 5-20 minutes
        END;

        -- Generate moves based on game type and duration
        SET @base_moves = CASE
            WHEN p_game_id = @battleship_id THEN 30 + FLOOR(RAND() * 40)  -- 30-70 moves
            WHEN p_game_id = @chess_id THEN 20 + FLOOR(RAND() * 60)       -- 20-80 moves
            WHEN p_game_id = @go_id THEN 40 + FLOOR(RAND() * 100)         -- 40-140 moves
            ELSE 5 + FLOOR(RAND() * 15)                                    -- 5-20 moves
        END;

        -- Determine result based on skill difference and randomness
        SET @skill_diff = @player_skill - RAND();  -- Compare against random opponent skill

        IF @can_draw AND ABS(@skill_diff) < 0.1 AND RAND() < 0.2 THEN
            SET @result = 'draw';
            SET @winner_id = NULL;
        ELSE
            IF @skill_diff > 0 THEN  -- Player is more skilled
                IF RAND() < (0.5 + @skill_diff) THEN  -- Higher chance of winning
                    SET @result = 'win';
                    SET @winner_id = p_player_id;
                ELSE
                    SET @result = 'loss';
                    SET @winner_id = @opponent_id;
                END IF;
            ELSE  -- Opponent is more skilled
                IF RAND() < (0.5 - @skill_diff) THEN  -- Lower chance of winning
                    SET @result = 'loss';
                    SET @winner_id = @opponent_id;
                ELSE
                    SET @result = 'win';
                    SET @winner_id = p_player_id;
                END IF;
            END IF;
        END IF;

        -- Generate timestamp within date range
        SET @days_range = DATEDIFF(@max_date, @min_date);
        SET @random_days = FLOOR(RAND() * @days_range);
        SET @start_time = DATE_ADD(@min_date, INTERVAL @random_days DAY);
        SET @start_time = DATE_ADD(@start_time,
            INTERVAL FLOOR(RAND() * 24) HOUR);
        SET @end_time = DATE_ADD(@start_time,
            INTERVAL @base_duration MINUTE);

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
            @base_duration,
            @result
        );

        -- Insert move records with realistic variations
        SET @p1_moves = @base_moves + FLOOR(RAND() * 10) - 5; -- ±5 moves variation
        SET @p2_moves = @base_moves + FLOOR(RAND() * 10) - 5;

        INSERT INTO match_moves (move_id, match_id, player_id, moves_count)
VALUES
(UUID_TO_BIN(UUID()), match_id, p_player_id, @p1_moves),
(UUID_TO_BIN(UUID()), match_id, @opponent_id, @p2_moves);

        SET i = i + 1;
    END WHILE;
END //

-- Enhanced procedure to generate player statistics and ML targets
CREATE PROCEDURE generate_player_game_stats()
BEGIN

    -- Insert stats with ML target variables using proper grouping
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
        last_played,
        is_churned,
        engagement_level,
        player_level,
        win_probability
    )
        SELECT DISTINCT -- Ensure uniqueness
    UUID_TO_BIN(UUID()) AS stat_id,
    p.player_id,
    g.game_id,
    COUNT(DISTINCT m.match_id) AS total_games_played,
    SUM(CASE WHEN m.winner_id = p.player_id THEN 1 ELSE 0 END) AS total_wins,
    SUM(CASE WHEN m.winner_id IS NOT NULL AND m.winner_id != p.player_id THEN 1 ELSE 0 END) AS total_losses,
    SUM(CASE WHEN m.winner_id IS NULL THEN 1 ELSE 0 END) AS total_draws,
    COALESCE(SUM(mm.moves_count), 0) AS total_moves,
    COALESCE(SUM(m.duration_minutes), 0) AS total_time_played_minutes,
    MAX(m.end_time) AS last_played,
    -- Calculate win ratio and churn
    CASE
        WHEN COUNT(DISTINCT m.match_id) < 10 OR
             (SUM(CASE WHEN m.winner_id = p.player_id THEN 1 ELSE 0 END) /
              NULLIF(COUNT(DISTINCT m.match_id), 0)) < 0.2
        THEN TRUE
        ELSE FALSE
    END AS is_churned,
    -- Simplified engagement level based on play patterns
    GREATEST(0, LEAST(100,
        COALESCE(
            (SUM(m.duration_minutes) / NULLIF(COUNT(DISTINCT m.match_id), 0)) *
            (COUNT(DISTINCT m.match_id) / GREATEST(1, DATEDIFF(CURRENT_TIMESTAMP, MIN(m.start_time)))),
            0
        )
    )) AS engagement_level,
        -- Player level
        CASE
            WHEN COUNT(DISTINCT m.match_id) < 10 THEN 'novice'
            WHEN (SUM(CASE WHEN m.winner_id = p.player_id THEN 1 ELSE 0 END) * 100.0 /
                  NULLIF(COUNT(DISTINCT m.match_id), 0)) > 65
                AND COUNT(DISTINCT m.match_id) >= 50 THEN 'expert'
            ELSE 'intermediate'
        END AS player_level,
        -- Win probability
        GREATEST(0.1, LEAST(0.9,
            COALESCE(
                AVG(CASE
                    WHEN m.winner_id = p.player_id THEN 1
                    WHEN m.winner_id IS NULL THEN 0.5
                    ELSE 0
                END),
                0.5
            )
        )) AS win_probability
    FROM
        players p
        CROSS JOIN games g
        LEFT JOIN match_history m ON (m.player1_id = p.player_id OR m.player2_id = p.player_id)
            AND m.game_id = g.game_id
        LEFT JOIN match_moves mm ON mm.match_id = m.match_id AND mm.player_id = p.player_id
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
            WHEN s.total_games_played < 5 THEN
                1 + FLOOR(RAND() * 2)  -- New players get 1-2 rating
            ELSE
                GREATEST(1, LEAST(5,  -- Ensure rating is between 1 and 5
                    FLOOR(
                        (
                            -- Win ratio contribution (40%)
                            (s.total_wins * 100.0 / s.total_games_played * 0.4) +
                            -- Games played contribution (30%)
                            (CASE
                                WHEN s.total_games_played >= 100 THEN 100
                                ELSE s.total_games_played
                             END * 0.3) +
                            -- Time played contribution (20%)
                            (CASE
                                WHEN s.total_time_played_minutes >= 1000 THEN 100
                                ELSE s.total_time_played_minutes / 10
                             END * 0.2) +
                            -- Random factor (10%) for variety
                            (RAND() * 100 * 0.1)
                        ) / 20  -- Scale to 1-5 range
                    )
                ))
        END AS rating,
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