# Game Player Analytics

Retention, A/B test and player segmentation on two public mobile-game datasets (Kaggle).
SQL (DuckDB) for the KPIs, Python for the statistics, Power BI for the one-page dashboard.

**Dashboard:** [`docs/dashboard.pdf`](docs/dashboard.pdf) · Power BI file: `dashboard/game-player-analytics.pbix`

## Key results

| Question | Answer |
|---|---|
| Does moving the first gate from level 30 to 40 change retention? | **Day 7: yes, slightly worse.** 19.0% (gate_30) vs 18.2% (gate_40), p = 0.0016, bootstrap CI excludes 0. **Day 1: inconclusive** (44.8% vs 44.2%, p = 0.074). |
| Recommendation | Keep the gate at level 30. |
| How does engagement relate to retention? | Day-7 retention rises from 0.7% (0 rounds) to 55.0% (50+ rounds). This is a correlation: playing a lot is partly a consequence of staying. |
| Player segments | 3 segments: highly active non-payers (39%), low-activity non-payers (40%), payers (20%). |

## Method

1. **Module A, retention KPIs** (`sql/01_retention.sql`, `notebooks/01_retention.ipynb`): global KPIs, retention by version, engagement bands, quartiles with a window function, extreme-value check.
2. **Module B, A/B test** (`notebooks/02_ab_test.ipynb`): sample ratio mismatch check, two-proportion z-test, Wilson intervals, bootstrap (5,000 resamples, seed 42). Two indicators are tested, so the threshold is 0.025 (0.05 / 2).
3. **Module C, segmentation** (`notebooks/03_segmentation.ipynb`): K-means on 4 standardised variables, compared with a shuffled-columns baseline and checked for stability across seeds.
4. **Dashboard** (`scripts/export_dashboard_data.py`, `dashboard/`): the script recomputes the figures from `game.duckdb` and writes the CSVs used by Power BI.

## Limits

- The A/B test only measures retention, not revenue. A lower Day-7 retention does not give the revenue impact.
- The sample ratio mismatch check gives p = 0.0086: group sizes are slightly unbalanced, so the assignment should be verified before trusting the result in production.
- One player has 49,854 rounds (next: 2,961). Kept in retention rates, excluded from analyses on round counts.
- **The behaviour dataset looks simulated** (near-zero correlations, uniform distributions). The segments mostly separate payers from non-payers and session frequency, and the silhouette score is no better than on shuffled data. They demonstrate the method; they are not findings about real players. The suggested actions are hypotheses, not tested.

## Reproduce

```powershell
# download the two CSV files (links in data/README.md) into data/raw/
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install duckdb pandas numpy scipy statsmodels scikit-learn jupyter
# run notebooks/00_exploration.ipynb first (creates game.duckdb), then 01, 02, 03
python scripts/export_dashboard_data.py
```

Data sources and licences: see [`data/README.md`](data/README.md).
