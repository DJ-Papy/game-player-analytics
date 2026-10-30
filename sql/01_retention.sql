-- =====================================================================
-- Module A - Player retention and engagement KPIs
-- Engine: DuckDB | Table: cookie_cats (90,189 players, one row per player)
-- Columns: userid, version (gate_30 / gate_40), sum_gamerounds (rounds
--          played during the first week), retention_1, retention_7 (booleans)
-- =====================================================================


-- 1. Global KPIs
-- A boolean cast to INT is 0 or 1, so AVG() gives the share of players
-- who came back. Multiplied by 100 it becomes a retention rate in %.
SELECT
  COUNT(*)                              AS players,
  ROUND(100 * AVG(retention_1::INT), 2) AS retention_d1_pct,
  ROUND(100 * AVG(retention_7::INT), 2) AS retention_d7_pct
FROM cookie_cats;


-- 2. Retention by game version (A/B test groups)
-- GROUP BY splits the same calculation between gate_30 and gate_40.
-- This is only a description: the statistical test comes in module B.
SELECT
  version,
  COUNT(*)                              AS players,
  ROUND(100 * AVG(retention_1::INT), 2) AS retention_d1_pct,
  ROUND(100 * AVG(retention_7::INT), 2) AS retention_d7_pct
FROM cookie_cats
GROUP BY version
ORDER BY version;


-- 3. Engagement funnel: Day-7 retention by number of rounds played
-- CASE WHEN builds engagement bands. Players with 0 rounds installed
-- the game but never played. Retention rises sharply with engagement,
-- but this is a correlation: playing a lot is partly a consequence of staying.
SELECT
  CASE
    WHEN sum_gamerounds = 0   THEN '0 rounds'
    WHEN sum_gamerounds <= 5  THEN '1-5'
    WHEN sum_gamerounds <= 20 THEN '6-20'
    WHEN sum_gamerounds <= 50 THEN '21-50'
    ELSE '50+'
  END AS band,
  COUNT(*)                              AS players,
  ROUND(100 * AVG(retention_7::INT), 2) AS retention_d7_pct
FROM cookie_cats
GROUP BY band
ORDER BY MIN(sum_gamerounds);


-- 4. Engagement quartiles (window function)
-- NTILE(4) OVER (...) sorts players by rounds played and cuts them into
-- 4 groups of equal size, without collapsing the rows like GROUP BY would.
-- Note: players with the same number of rounds (5 or 16 here) can fall in
-- two different quartiles, so bounds can overlap by one value.
WITH quartiles AS (
  SELECT *, NTILE(4) OVER (ORDER BY sum_gamerounds) AS quartile
  FROM cookie_cats
)
SELECT
  quartile,
  COUNT(*)            AS players,
  MIN(sum_gamerounds) AS min_rounds,
  MAX(sum_gamerounds) AS max_rounds,
  ROUND(100 * AVG(retention_7::INT), 2) AS retention_d7_pct
FROM quartiles
GROUP BY quartile
ORDER BY quartile;


-- 5. Extreme values check
-- One player has 49,854 rounds, about 17 times the next one (2,961).
-- Cause unknown (error, bot or real player). Decision: keep this player
-- in retention rates (1 player out of 90,189 has no effect) but exclude
-- from any analysis using the number of rounds (averages, clustering).
SELECT userid, version, sum_gamerounds
FROM cookie_cats
ORDER BY sum_gamerounds DESC
LIMIT 10;
