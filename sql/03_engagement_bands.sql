-- D7 retention by rounds played during the first 14 days after install.
-- Correlation only, and partly mechanical: a player who comes back on day 7 has more days
-- left to play. Bands are fixed in advance so that each holds a meaningful share of players.
SELECT
  ROW_NUMBER() OVER (ORDER BY MIN(sum_gamerounds)) AS sort_order,
  CASE
    WHEN sum_gamerounds = 0   THEN '0 rounds'
    WHEN sum_gamerounds <= 5  THEN '1-5'
    WHEN sum_gamerounds <= 20 THEN '6-20'
    WHEN sum_gamerounds <= 50 THEN '21-50'
    ELSE '50+'
  END                                              AS band,
  COUNT(*)                                         AS players,
  AVG(retention_7::INT)                            AS retention_d7
FROM cookie_cats
GROUP BY band
ORDER BY sort_order;
