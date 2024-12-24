-- Schema Changes for Foreign Keys

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

-- Match Moves Foreign Keys
ALTER TABLE match_moves
    DROP FOREIGN KEY match_moves_ibfk_1,
    DROP FOREIGN KEY match_moves_ibfk_2;

ALTER TABLE match_moves
    ADD CONSTRAINT match_moves_match_fk
        FOREIGN KEY (match_id)
        REFERENCES match_history (match_id)
        ON DELETE CASCADE
        ON UPDATE CASCADE,
    ADD CONSTRAINT match_moves_player_fk
        FOREIGN KEY (player_id)
        REFERENCES players (player_id)
        ON DELETE CASCADE
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

-- Player Ratings Foreign Keys
ALTER TABLE player_ratings
    DROP FOREIGN KEY player_ratings_ibfk_1,
    DROP FOREIGN KEY player_ratings_ibfk_2;

ALTER TABLE player_ratings
    ADD CONSTRAINT player_ratings_player_fk
        FOREIGN KEY (player_id)
        REFERENCES players (player_id)
        ON DELETE CASCADE
        ON UPDATE CASCADE,
    ADD CONSTRAINT player_ratings_game_fk
        FOREIGN KEY (game_id)
        REFERENCES games (game_id)
        ON DELETE CASCADE
        ON UPDATE CASCADE;