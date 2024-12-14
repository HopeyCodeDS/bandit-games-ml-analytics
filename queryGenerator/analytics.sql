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

