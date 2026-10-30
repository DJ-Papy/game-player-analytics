# Data sources

Raw files are kept in `data/raw/`. They are public datasets, not data from any game studio.

## cookie_cats.csv
- Content: A/B test of a mobile puzzle game (first gate moved from level 30 to level 40). 90,189 players.
- Columns: userid, version, sum_gamerounds, retention_1, retention_7.
- Source: Kaggle ("Mobile Games A/B Testing - Cookie Cats"), originally published by DataCamp.
- URL: https://www.kaggle.com/datasets/mursideyarkin/mobile-games-ab-testing-cookie-cats
- Licence: not stated on the Kaggle page (checked 2026-10-30). Original data from DataCamp. Do not republish the CSV; keep it out of git and link the source instead.
- Downloaded on: 2026-10-29

## online_gaming_behavior_insights.csv
- Content: player behaviour (sessions, playtime, purchases, level, engagement label). 40,034 players.
- Source: Kaggle ("Predict Online Gaming Behavior Dataset").
- URL: https://www.kaggle.com/datasets/wasiqaliyasir/online-gaming-behavior-insight
- Licence: MIT
- Downloaded on: 2026-10-29
- Note: the variables look independent and uniformly distributed (near-zero correlations), which is typical of simulated data. See `notebooks/03_segmentation.ipynb`.
