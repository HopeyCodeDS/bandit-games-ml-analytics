# TRUNCATE TABLE players;

SET FOREIGN_KEY_CHECKS = 0;
TRUNCATE TABLE players;
SET FOREIGN_KEY_CHECKS = 1;

SET FOREIGN_KEY_CHECKS = 0;
TRUNCATE TABLE games;
SET FOREIGN_KEY_CHECKS = 1;

SET FOREIGN_KEY_CHECKS = 0;
TRUNCATE TABLE match_history;
SET FOREIGN_KEY_CHECKS = 1;

SET FOREIGN_KEY_CHECKS = 0;
TRUNCATE TABLE player_game_stats;
SET FOREIGN_KEY_CHECKS = 1;

SET FOREIGN_KEY_CHECKS = 0;
TRUNCATE TABLE players_audit;
SET FOREIGN_KEY_CHECKS = 1;


SET FOREIGN_KEY_CHECKS = 0;
TRUNCATE TABLE games_audit;
SET FOREIGN_KEY_CHECKS = 1;


# SET FOREIGN_KEY_CHECKS = 0;
# TRUNCATE TABLE matches_audit;
# SET FOREIGN_KEY_CHECKS = 1;


SET FOREIGN_KEY_CHECKS = 0;
TRUNCATE TABLE player_game_stats_audit;
SET FOREIGN_KEY_CHECKS = 1;

# temp_last_played

USE game_analytics;

-- Truncate all tables
SET FOREIGN_KEY_CHECKS = 0;
-- Generate truncate table statements
SELECT CONCAT('TRUNCATE TABLE `', table_name, '`;')
FROM information_schema.tables
WHERE table_schema = 'game_analytics';
SET FOREIGN_KEY_CHECKS = 1;


USE game_analytics;
SHOW TABLES;


SELECT
   g.name as game_name,
   p.username,
   COUNT(m.match_id) as total_matches,
   COUNT(CASE WHEN m.player1_id = p.player_id THEN 1 END) as games_as_player1,
   COUNT(CASE WHEN m.player2_id = p.player_id THEN 1 END) as games_as_player2
FROM players p
CROSS JOIN games g
LEFT JOIN matches m ON
   (m.player1_id = p.player_id OR m.player2_id = p.player_id)
   AND m.game_id = g.game_id
GROUP BY g.name, p.username
ORDER BY g.name, total_matches DESC;

select g.game_id,g.name,count(*)
from games g
left join game_analytics.player_game_stats pgs on g.game_id = pgs.game_id
group by g.game_id ;




# DROP TABLES;

SET FOREIGN_KEY_CHECKS = 0;
DROP TABLE players;
SET FOREIGN_KEY_CHECKS = 1;


SET FOREIGN_KEY_CHECKS = 0;
DROP TABLE match_history;
SET FOREIGN_KEY_CHECKS = 1;

SET FOREIGN_KEY_CHECKS = 0;
DROP TABLE games;
SET FOREIGN_KEY_CHECKS = 1;

SET FOREIGN_KEY_CHECKS = 0;
DROP TABLE player_game_stats;
SET FOREIGN_KEY_CHECKS = 1;

SET FOREIGN_KEY_CHECKS = 0;
DROP TABLE games_audit;
SET FOREIGN_KEY_CHECKS = 1;


SET FOREIGN_KEY_CHECKS = 0;
DROP TABLE players_audit;
SET FOREIGN_KEY_CHECKS = 1;


# SET FOREIGN_KEY_CHECKS = 0;
# DROP TABLE matches_audit;
# SET FOREIGN_KEY_CHECKS = 1;



SET FOREIGN_KEY_CHECKS = 0;
DROP TABLE player_game_stats_audit;
SET FOREIGN_KEY_CHECKS = 1;
