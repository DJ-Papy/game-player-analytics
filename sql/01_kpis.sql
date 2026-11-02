-- Headline retention of the A/B test population (cookie_cats: one row per player).
-- Rates are fractions; the notebooks and the dashboard format them as percentages.
SELECT
  COUNT(*)                            AS players,
  COUNT(*) FILTER (WHERE retention_1) AS retained_d1,
  COUNT(*) FILTER (WHERE retention_7) AS retained_d7,
  AVG(retention_1::INT)               AS retention_d1,
  AVG(retention_7::INT)               AS retention_d7
FROM cookie_cats;
