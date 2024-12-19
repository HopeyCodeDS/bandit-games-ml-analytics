-- Match History Foreign Keys
ALTER TABLE match_history
    DROP FOREIGN KEY match_history_ibfk_1,
    DROP FOREIGN KEY match_history_ibfk_2,
    DROP FOREIGN KEY match_history_ibfk_3,
    DROP FOREIGN KEY match_history_ibfk_4;

ALTER TABLE match_history
    ADD CONSTRAINT match_history_game_fk
        FOREIGN KEY (game_id)
        REFERENCES games (game_id)
        ON DELETE CASCADE
        ON UPDATE CASCADE,
    ADD CONSTRAINT match_history_player1_fk
        FOREIGN KEY (player1_id)
        REFERENCES players (player_id)
        ON DELETE CASCADE
        ON UPDATE CASCADE,
    ADD CONSTRAINT match_history_player2_fk
        FOREIGN KEY (player2_id)
        REFERENCES players (player_id)
        ON DELETE CASCADE
        ON UPDATE CASCADE,
    ADD CONSTRAINT match_history_winner_fk
        FOREIGN KEY (winner_id)
        REFERENCES players (player_id)
        ON DELETE SET NULL
        ON UPDATE CASCADE;

-- Player Game Stats Foreign Keys
ALTER TABLE player_game_stats
    DROP FOREIGN KEY player_game_stats_ibfk_1,
    DROP FOREIGN KEY player_game_stats_ibfk_2;

ALTER TABLE player_game_stats
    ADD CONSTRAINT player_game_stats_player_fk
        FOREIGN KEY (player_id)
        REFERENCES players (player_id)
        ON DELETE CASCADE
        ON UPDATE CASCADE,
    ADD CONSTRAINT player_game_stats_game_fk
        FOREIGN KEY (game_id)
        REFERENCES games (game_id)
        ON DELETE CASCADE
        ON UPDATE CASCADE;