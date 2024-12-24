DELIMITER //

-- Match History Triggers
CREATE TRIGGER match_history_after_insert
AFTER INSERT ON match_history
FOR EACH ROW
BEGIN
    -- Update player game stats for both players
    CALL update_player_game_stats(NEW.player1_id, NEW.game_id);
    CALL update_player_game_stats(NEW.player2_id, NEW.game_id);
END//

CREATE TRIGGER match_history_after_update
AFTER UPDATE ON match_history
FOR EACH ROW
BEGIN
    -- Update stats if winner or result changes
    IF NEW.winner_id != OLD.winner_id OR NEW.result != OLD.result THEN
        CALL update_player_game_stats(NEW.player1_id, NEW.game_id);
        CALL update_player_game_stats(NEW.player2_id, NEW.game_id);
    END IF;
END//

CREATE TRIGGER match_history_after_delete
AFTER DELETE ON match_history
FOR EACH ROW
BEGIN
    -- Update stats for both players
    CALL update_player_game_stats(OLD.player1_id, OLD.game_id);
    CALL update_player_game_stats(OLD.player2_id, OLD.game_id);
END//

-- Helper procedure to update player statistics
CREATE PROCEDURE update_player_game_stats(
    IN p_player_id BINARY(16),
    IN p_game_id BINARY(16)
)
BEGIN
    DECLARE v_total_games INT;
    DECLARE v_total_wins INT;
    DECLARE v_total_losses INT;
    DECLARE v_total_draws INT;
    DECLARE v_total_moves INT;
    DECLARE v_total_time INT;
    DECLARE v_last_played TIMESTAMP;
    DECLARE v_stat_id BINARY(16);

    -- Calculate match statistics
    SELECT
        COUNT(DISTINCT m.match_id),
        SUM(CASE WHEN m.winner_id = p_player_id THEN 1 ELSE 0 END),
        SUM(CASE WHEN m.winner_id IS NOT NULL AND m.winner_id != p_player_id THEN 1 ELSE 0 END),
        SUM(CASE WHEN m.winner_id IS NULL THEN 1 ELSE 0 END),
        SUM(mm.moves_count),
        SUM(m.duration_minutes),
        MAX(m.end_time)
    INTO
        v_total_games,
        v_total_wins,
        v_total_losses,
        v_total_draws,
        v_total_moves,
        v_total_time,
        v_last_played
    FROM match_history m
    LEFT JOIN match_moves mm ON mm.match_id = m.match_id AND mm.player_id = p_player_id
    WHERE (m.player1_id = p_player_id OR m.player2_id = p_player_id)
    AND m.game_id = p_game_id;

    -- Get existing stat_id if any
    SELECT stat_id INTO v_stat_id
    FROM player_game_stats
    WHERE player_id = p_player_id AND game_id = p_game_id;

    -- Insert or update player_game_stats
    IF v_stat_id IS NULL THEN
        SET v_stat_id = UUID_TO_BIN(UUID());
    END IF;

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
        -- Compute ML target variables
        is_churned,
        engagement_level,
        player_level,
        win_probability
    ) VALUES (
        v_stat_id,
        p_player_id,
        p_game_id,
        COALESCE(v_total_games, 0),
        COALESCE(v_total_wins, 0),
        COALESCE(v_total_losses, 0),
        COALESCE(v_total_draws, 0),
        COALESCE(v_total_moves, 0),
        COALESCE(v_total_time, 0),
        v_last_played,
        -- Compute churn based on activity
        CASE
            WHEN v_last_played IS NULL THEN TRUE
            WHEN DATEDIFF(CURRENT_TIMESTAMP, v_last_played) > 30 THEN TRUE
            ELSE FALSE
        END,
        -- Compute engagement level (0-100)
        CASE
            WHEN v_total_games IS NULL THEN 0
            ELSE
                GREATEST(0, LEAST(100,
                    (COALESCE(v_total_games, 0) * 40 / 100) +  -- Games played component
                    (CASE  -- Recency component
                        WHEN v_last_played IS NULL THEN 0
                        WHEN DATEDIFF(CURRENT_TIMESTAMP, v_last_played) < 7 THEN 40
                        WHEN DATEDIFF(CURRENT_TIMESTAMP, v_last_played) < 14 THEN 30
                        WHEN DATEDIFF(CURRENT_TIMESTAMP, v_last_played) < 30 THEN 20
                        ELSE 0
                    END) +
                    (COALESCE(v_total_time, 0) * 20 / 1000)  -- Time played component
                ))
        END,
        -- Compute player level
        CASE
            WHEN v_total_games < 10 THEN 'novice'
            WHEN (v_total_wins * 100.0 / NULLIF(v_total_games, 0)) > 65
                AND v_total_games >= 50 THEN 'expert'
            ELSE 'intermediate'
        END,
        -- Compute win probability
        GREATEST(0.1, LEAST(0.9,
            COALESCE(v_total_wins * 1.0 / NULLIF(v_total_games, 0), 0.5)
        ))
    )
    ON DUPLICATE KEY UPDATE
        total_games_played = VALUES(total_games_played),
        total_wins = VALUES(total_wins),
        total_losses = VALUES(total_losses),
        total_draws = VALUES(total_draws),
        total_moves = VALUES(total_moves),
        total_time_played_minutes = VALUES(total_time_played_minutes),
        last_played = VALUES(last_played),
        is_churned = VALUES(is_churned),
        engagement_level = VALUES(engagement_level),
        player_level = VALUES(player_level),
        win_probability = VALUES(win_probability);

    -- Update player rating
    INSERT INTO player_ratings (
        rating_id,
        player_id,
        game_id,
        rating,
        rating_date
    )
    SELECT
        UUID_TO_BIN(UUID()),
        p_player_id,
        p_game_id,
        CASE
            WHEN v_total_games < 5 THEN 1
            ELSE
                GREATEST(1, LEAST(5,
                    FLOOR(
                        (
                            (COALESCE(v_total_wins, 0) * 100.0 / NULLIF(v_total_games, 0) * 0.4) +
                            (CASE
                                WHEN v_total_games >= 100 THEN 100
                                ELSE v_total_games
                             END * 0.3) +
                            (CASE
                                WHEN v_total_time >= 1000 THEN 100
                                ELSE v_total_time / 10
                             END * 0.3)
                        ) / 20
                    )
                ))
        END,
        CURRENT_TIMESTAMP;
END//

DELIMITER ;


# DROP PROCEDURE IF EXISTS update_player_game_stats;

# DROP TRIGGER IF EXISTS match_history_after_insert;
# DROP TRIGGER IF EXISTS match_history_after_update;
# DROP TRIGGER IF EXISTS match_history_after_delete;