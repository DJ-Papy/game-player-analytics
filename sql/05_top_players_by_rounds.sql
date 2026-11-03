-- Extreme values. One player has 49,854 rounds, about 17 times the next one (2,961):
-- error, bot or real player, the cause is unknown. Decision: kept in retention rates
-- (1 player out of 90,189), excluded from any statistic on the number of rounds.
SELECT userid, version, sum_gamerounds
FROM cookie_cats
ORDER BY sum_gamerounds DESC
LIMIT 10;
