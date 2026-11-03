-- D7 retention by quartile of rounds played. NTILE gives groups of equal size, so players
-- with the same number of rounds (5, 16, 51) can sit on both sides of a boundary.
WITH quartiles AS (
  SELECT *, NTILE(4) OVER (ORDER BY sum_gamerounds, userid) AS quartile
  FROM cookie_cats
)
SELECT
  quartile,
  COUNT(*)              AS players,
  MIN(sum_gamerounds)   AS min_rounds,
  MAX(sum_gamerounds)   AS max_rounds,
  AVG(retention_7::INT) AS retention_d7
FROM quartiles
GROUP BY quartile
ORDER BY quartile;
