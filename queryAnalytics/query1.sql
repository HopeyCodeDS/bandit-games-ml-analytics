-- Get top players for Battleship
SELECT p.username, pgs.wins, pgs.win_ratio
FROM players p
JOIN player_game_stats pgs ON p.player_id = pgs.player_id
JOIN games g ON pgs.game_id = g.game_id
WHERE g.game_name = 'Battleship'
ORDER BY pgs.win_ratio DESC
LIMIT 10;

-- Get most popular games
SELECT g.game_name, SUM(pgs.total_games_played) as total_matches
FROM games g
JOIN player_game_stats pgs ON g.game_id = pgs.game_id
GROUP BY g.game_name
ORDER BY total_matches DESC;

-- Get player activity by country
SELECT location, COUNT(*) as player_count,
       AVG(total_games_played) as avg_games_played
FROM players p
JOIN player_game_stats pgs ON p.player_id = pgs.player_id
GROUP BY location
ORDER BY player_count DESC;


---------------------------------------------------------
