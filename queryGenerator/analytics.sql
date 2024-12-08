-- Get top players for Battleship
WITH battleship_stats AS (
    SELECT
        BIN_TO_UUID(pgs.player_id) as player_id,
        p.username,
        p.country,
        pgs.total_games_played,
        SUM(CASE WHEN pgs.result = 'WIN' THEN 1 ELSE 0 END) as total_wins,
        pgs.win_ratio,
        pgs.total_hits,
        pgs.total_misses,
        pgs.highest_score,
        pgs.player_level,
        -- Calculate hit accuracy
        ROUND((pgs.total_hits / (pgs.total_hits + pgs.total_misses)) * 100, 2) as accuracy_percentage,
        -- Calculate average moves per game
        ROUND(pgs.total_moves / pgs.total_games_played, 2) as avg_moves_per_game,
        pgs.rating
    FROM game_analytics.player_game_stats pgs
    INNER JOIN game_analytics.players p ON p.player_id = pgs.player_id
    INNER JOIN game_analytics.games g ON g.game_id = pgs.game_id
    WHERE g.name = 'Battleship'
        AND pgs.total_games_played >= 10  -- Minimum games threshold
        AND pgs.churned = 'NO'           -- Only active players
    GROUP BY
        pgs.player_id,
        p.username,
        p.country,
        pgs.total_games_played,
        pgs.win_ratio,
        pgs.total_hits,
        pgs.total_misses,
        pgs.highest_score,
        pgs.player_level,
        pgs.total_moves,
        pgs.rating
)
SELECT
    username,
    country,
    player_level,
    total_games_played,
    total_wins,
    win_ratio,
    accuracy_percentage,
    avg_moves_per_game,
    highest_score,
    rating
FROM battleship_stats
ORDER BY
    win_ratio DESC,
    accuracy_percentage DESC,
    highest_score DESC
LIMIT 100;

-- Get most popular games
SELECT g.name, SUM(pgs.total_games_played) as total_matches
FROM games g
JOIN player_game_stats pgs ON g.game_id = pgs.game_id
GROUP BY g.name
ORDER BY total_matches DESC;

-- Get player activity by country
SELECT country, COUNT(*) as player_count,
       AVG(total_games_played) as avg_games_played
FROM players p
JOIN player_game_stats pgs ON p.player_id = pgs.player_id
GROUP BY country
ORDER BY player_count DESC;


---------------------------------------------------------
