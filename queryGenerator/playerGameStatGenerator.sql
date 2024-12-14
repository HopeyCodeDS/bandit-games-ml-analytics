WITH player_stats AS (
    SELECT
        BIN_TO_UUID(pgs.player_id) as player_id,
        p.username,
        p.age,
        p.country,
        p.gender,
        g.name as game_name,
        BIN_TO_UUID(pgs.game_id) as game_id,
        pgs.total_games_played,
        -- Calculate total wins and losses
        SUM(CASE WHEN pgs.result = 'WIN' THEN 1 ELSE 0 END) as total_wins,
        SUM(CASE WHEN pgs.result = 'LOSS' THEN 1 ELSE 0 END) as total_losses,
        pgs.win_ratio,
        pgs.total_moves,
        pgs.highest_score,
        pgs.rating,
        pgs.churned,
        pgs.player_level,
        pgs.last_played
    FROM game_analytics.player_game_stats pgs
    INNER JOIN game_analytics.players p ON p.player_id = pgs.player_id
    INNER JOIN game_analytics.games g ON g.game_id = pgs.game_id
    GROUP BY
        pgs.player_id,
        p.username,
        p.age,
        p.country,
        p.gender,
        g.name,
        pgs.game_id,
        pgs.total_games_played,
        pgs.win_ratio,
        pgs.total_moves,
        pgs.highest_score,
        pgs.rating,
        pgs.churned,
        pgs.player_level,
        pgs.last_played
)
SELECT *
FROM player_stats;

