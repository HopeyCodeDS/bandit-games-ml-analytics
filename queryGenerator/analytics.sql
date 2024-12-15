-- Get top players for Battleship
SELECT
    pgs.player_name,
    pgs.country,
    pgs.total_games_played,
    pgs.total_wins,
    pgs.total_losses,
    ROUND((pgs.total_wins * 100.0 / pgs.total_games_played), 2) as win_rate,
    pgs.total_moves,
    pgs.total_time_played_minutes
FROM player_game_stats pgs
WHERE pgs.game_name = 'battleship'
    AND pgs.total_games_played >= 20  -- Only consider players with significant games
ORDER BY win_rate DESC, total_games_played DESC
LIMIT 10;


-- Get most popular games
SELECT
    g.name as game_name,
    COUNT(DISTINCT m.match_id) as total_matches,
    COUNT(DISTINCT CASE WHEN m.player1_id = p.player_id THEN p.player_id
          WHEN m.player2_id = p.player_id THEN p.player_id END) as unique_players,
    ROUND(AVG(m.duration_minutes), 2) as avg_duration_minutes,
    ROUND(COUNT(DISTINCT m.match_id) * 100.0 / (SELECT COUNT(*) FROM match_history), 2) as match_percentage
FROM games g
LEFT JOIN match_history m ON g.game_id = m.game_id
LEFT JOIN players p ON p.player_id = m.player1_id OR p.player_id = m.player2_id
GROUP BY g.name
ORDER BY total_matches DESC;


-- Get player activity by country
SELECT
    p.country,
    COUNT(DISTINCT p.player_id) as total_players,
    COUNT(DISTINCT m.match_id) as total_matches,
    ROUND(COUNT(DISTINCT m.match_id) * 1.0 / COUNT(DISTINCT p.player_id), 2) as avg_matches_per_player,
    COUNT(DISTINCT m.game_name) as unique_games_played,
    ROUND(SUM(m.duration_minutes) / 60.0, 2) as total_hours_played,
    ROUND(SUM(CASE WHEN m.game_name = 'battleship' THEN 1 ELSE 0 END) * 100.0 /
          COUNT(DISTINCT m.match_id), 2) as battleship_percentage
FROM players p
LEFT JOIN match_history m ON p.player_id = m.player1_id OR p.player_id = m.player2_id
GROUP BY p.country
ORDER BY total_matches DESC;

-- Player retention and engagement patterns
SELECT
    game_name,
    COUNT(DISTINCT player_id) as active_players,
    ROUND(AVG(total_time_played_minutes/60), 2) as avg_hours_per_player,
    ROUND(AVG(total_games_played), 2) as avg_games_per_player,
    ROUND(MIN(total_games_played), 2) as min_games,
    ROUND(MAX(total_games_played), 2) as max_games
FROM player_game_stats
GROUP BY game_name
ORDER BY active_players DESC;

-- Player skill level distribution
WITH PlayerStats AS (
    SELECT
        p.player_id,
        p.gender,
        p.country,
        COUNT(DISTINCT m.game_name) as games_played,
        COUNT(*) as total_matches,
        SUM(CASE WHEN m.winner_id = p.player_id THEN 1 ELSE 0 END) as wins,
        ROUND(SUM(CASE WHEN m.winner_id = p.player_id THEN 1 ELSE 0 END) * 100.0 /
              COUNT(*), 2) as win_rate
    FROM players p
    JOIN match_history m ON (p.player_id = m.player1_id OR p.player_id = m.player2_id)
    GROUP BY p.player_id, p.gender, p.country
)
SELECT
    CASE
        WHEN win_rate >= 55 THEN 'Expert'
        WHEN win_rate >= 45 THEN 'Intermediate'
        ELSE 'Beginner'
    END as skill_level,
    COUNT(*) as player_count,
    ROUND(AVG(win_rate), 2) as avg_win_rate,
    ROUND(AVG(total_matches), 2) as avg_matches_played,
    ROUND(AVG(games_played), 2) as avg_different_games
FROM PlayerStats
GROUP BY
    CASE
        WHEN win_rate >= 55 THEN 'Expert'
        WHEN win_rate >= 45 THEN 'Intermediate'
        ELSE 'Beginner'
    END
ORDER BY avg_win_rate DESC;

-- Analysis of player matching patterns
SELECT
    p1.country as player1_country,
    p2.country as player2_country,
    COUNT(*) as match_count,
    ROUND(AVG(m.duration_minutes), 2) as avg_duration,
    COUNT(DISTINCT m.game_name) as unique_games
FROM match_history m
JOIN players p1 ON m.player1_id = p1.player_id
JOIN players p2 ON m.player2_id = p2.player_id
GROUP BY p1.country, p2.country
HAVING match_count > 100
ORDER BY match_count DESC;

-- Analyzing game complexity through moves and duration
SELECT
    game_name,
    ROUND(AVG(player1_moves + player2_moves), 2) as avg_total_moves,
    ROUND(AVG(duration_minutes), 2) as avg_duration,
    ROUND(AVG((player1_moves + player2_moves) / duration_minutes), 2) as moves_per_minute,
    COUNT(*) as total_matches
FROM match_history
GROUP BY game_name
ORDER BY moves_per_minute DESC;

-- Analyzing players who play multiple games
WITH PlayerGameCounts AS (
    SELECT
        p.player_id,
        p.gender,
        p.country,
        COUNT(DISTINCT pgs.game_name) as games_played,
        GROUP_CONCAT(DISTINCT pgs.game_name) as game_list
    FROM players p
    JOIN player_game_stats pgs ON p.player_id = pgs.player_id
    GROUP BY p.player_id, p.gender, p.country
)
SELECT
    games_played as number_of_games,
    COUNT(*) as player_count,
    ROUND(COUNT(*) * 100.0 / (SELECT COUNT(*) FROM players), 2) as percentage_of_players
FROM PlayerGameCounts
GROUP BY games_played
ORDER BY games_played;


# ---------------------------------------------------------

select game_name, count(*)
from match_history
group by game_name ;

select game_name, count(*)
from player_game_stats
group by game_name;

SELECT
    game_name,
    COUNT(*) as total_matches,
    ROUND(COUNT(*) * 100.0 / (SELECT COUNT(*) FROM match_history), 2) as percentage
FROM match_history
GROUP BY game_name
ORDER BY total_matches DESC;

