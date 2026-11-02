-- Retention by A/B group. Descriptive only: the significance test is in game_players.ab_test.
SELECT
  version,
  COUNT(*)                            AS players,
  COUNT(*) FILTER (WHERE retention_1) AS retained_d1,
  COUNT(*) FILTER (WHERE retention_7) AS retained_d7,
  AVG(retention_1::INT)               AS retention_d1,
  AVG(retention_7::INT)               AS retention_d7
FROM cookie_cats
GROUP BY version
ORDER BY version;
