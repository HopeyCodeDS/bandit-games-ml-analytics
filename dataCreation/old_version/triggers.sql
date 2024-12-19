-- Triggers for games table updates
DELIMITER //

CREATE TRIGGER games_after_update
AFTER UPDATE ON games
FOR EACH ROW
BEGIN
    -- Update game_name in match_history
    IF NEW.name != OLD.name THEN
        UPDATE match_history
        SET game_name = NEW.name
        WHERE game_id = NEW.game_id;

        -- Update game_name in player_game_stats
        UPDATE player_game_stats
        SET game_name = NEW.name
        WHERE game_id = NEW.game_id;
    END IF;
END;//

-- Triggers for players table updates
CREATE TRIGGER players_after_update
AFTER UPDATE ON players
FOR EACH ROW
BEGIN
    -- Update player_name in player_game_stats
    IF NEW.firstname != OLD.firstname OR NEW.lastname != OLD.lastname THEN
        UPDATE player_game_stats
        SET player_name = CONCAT(NEW.firstname, ' ', NEW.lastname)
        WHERE player_id = NEW.player_id;
    END IF;

    -- Update other demographic information
    IF NEW.gender != OLD.gender OR NEW.country != OLD.country OR
       NEW.birthdate != OLD.birthdate THEN
        UPDATE player_game_stats
        SET gender = NEW.gender,
            country = NEW.country,
            age = TIMESTAMPDIFF(YEAR, NEW.birthdate, CURDATE())
        WHERE player_id = NEW.player_id;
    END IF;
END;//

-- Trigger for match_history updates to maintain player_game_stats
CREATE TRIGGER match_history_after_insert
AFTER INSERT ON match_history
FOR EACH ROW
BEGIN
    -- Update stats for player1
    CALL update_player_game_stats(NEW.player1_id, NEW.game_id);

    -- Update stats for player2
    CALL update_player_game_stats(NEW.player2_id, NEW.game_id);
END;//

-- Trigger for match_history deletions
CREATE TRIGGER match_history_after_delete
AFTER DELETE ON match_history
FOR EACH ROW
BEGIN
    -- Update stats for player1
    CALL update_player_game_stats(OLD.player1_id, OLD.game_id);

    -- Update stats for player2
    CALL update_player_game_stats(OLD.player2_id, OLD.game_id);
END;//

DELIMITER ;

-- Helper stored procedure to update player_game_stats
DELIMITER //

CREATE PROCEDURE update_player_game_stats(
    IN p_player_id BINARY(16),
    IN p_game_id BINARY(16)
)
BEGIN
    -- Get player information
    SELECT
        CONCAT(firstname, ' ', lastname),
        TIMESTAMPDIFF(YEAR, birthdate, CURDATE()),
        gender,
        country
    INTO
        @player_name,
        @age,
        @gender,
        @country
    FROM players
    WHERE player_id = p_player_id;

    -- Get game name
    SELECT name INTO @game_name
    FROM games
    WHERE game_id = p_game_id;

    -- Calculate updated statistics
    SELECT
        COUNT(*) as total_games,
        SUM(CASE WHEN winner_id = p_player_id THEN 1 ELSE 0 END) as wins,
        SUM(CASE WHEN winner_id IS NOT NULL AND winner_id != p_player_id THEN 1 ELSE 0 END) as losses,
        SUM(CASE WHEN player1_id = p_player_id THEN player1_moves ELSE player2_moves END) as total_moves,
        SUM(duration_minutes) as total_time,
        MAX(end_time) as last_played
    INTO
        @total_games,
        @wins,
        @losses,
        @total_moves,
        @total_time,
        @last_played
    FROM match_history
    WHERE (player1_id = p_player_id OR player2_id = p_player_id)
    AND game_id = p_game_id;

    -- Calculate win ratio
    SET @win_ratio = CASE
        WHEN @total_games > 0 THEN (@wins * 100.0 / @total_games)
        ELSE 0.00
    END;

    -- Insert or update player_game_stats
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
        win_ratio,
        last_played
    ) VALUES (
        UUID_TO_BIN(UUID()),
        p_player_id,
        @player_name,
        @age,
        @gender,
        @country,
        p_game_id,
        @game_name,
        @total_games,
        @wins,
        @losses,
        @total_moves,
        @total_time,
        @win_ratio,
        @last_played
    ) ON DUPLICATE KEY UPDATE
        player_name = @player_name,
        age = @age,
        gender = @gender,
        country = @country,
        game_name = @game_name,
        total_games_played = @total_games,
        total_wins = @wins,
        total_losses = @losses,
        total_moves = @total_moves,
        total_time_played_minutes = @total_time,
        win_ratio = @win_ratio,
        last_played = @last_played;
END;//

DELIMITER ;