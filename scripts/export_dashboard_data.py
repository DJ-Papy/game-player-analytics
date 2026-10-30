"""Export the results used by the Power BI dashboard.

Run from the project root (the folder that contains game.duckdb):
    python scripts/export_dashboard_data.py

Optional arguments: path to the DuckDB file, output folder.
CSV files use ';' as separator and ',' as decimal mark (French Power BI / Excel).
"""
import sys
from pathlib import Path

import duckdb
import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
from statsmodels.stats.proportion import proportion_confint, proportions_ztest

DB = sys.argv[1] if len(sys.argv) > 1 else "game.duckdb"
OUT = Path(sys.argv[2] if len(sys.argv) > 2 else "dashboard/data")
OUT.mkdir(parents=True, exist_ok=True)

ALPHA = 0.025          # two retention indicators are tested: threshold 0.05 / 2
N_BOOT = 5000
SEED = 42


def save(df: pd.DataFrame, name: str) -> None:
    df.to_csv(OUT / name, sep=";", decimal=",", index=False, encoding="utf-8")
    print(f"{name}: {len(df)} row(s)")


con = duckdb.connect(DB, read_only=True)

# ---------------------------------------------------------------- 1. global KPIs
kpi = con.sql("""
    SELECT COUNT(*)                    AS players,
           AVG(retention_1::INT)       AS retention_j1,
           AVG(retention_7::INT)       AS retention_j7
    FROM cookie_cats
""").df()
save(kpi, "kpi_global.csv")

# ---------------------------------------------- 2. retention by version (+ Wilson CI)
by_version = con.sql("""
    SELECT version,
           COUNT(*)              AS players,
           SUM(retention_1::INT) AS success_j1,
           SUM(retention_7::INT) AS success_j7
    FROM cookie_cats
    GROUP BY version
    ORDER BY version
""").df()

rows = []
for _, r in by_version.iterrows():
    for indicator, col in (("Day 1", "success_j1"), ("Day 7", "success_j7")):
        low, high = proportion_confint(r[col], r["players"], method="wilson")
        rows.append({"indicator": indicator, "version": r["version"], "players": int(r["players"]),
                     "retention": r[col] / r["players"], "ci_low": low, "ci_high": high})
save(pd.DataFrame(rows), "retention_by_version.csv")

# -------------------------------------------------- 3. A/B test (z-test + bootstrap)
df = con.sql("SELECT version, retention_1, retention_7 FROM cookie_cats").df()
results = []
for indicator, col in (("Day 1", "retention_1"), ("Day 7", "retention_7")):
    g = df.groupby("version")[col].agg(["sum", "count"])
    _, p_value = proportions_ztest(g["sum"].values, g["count"].values)
    rate = g["sum"] / g["count"]

    rng = np.random.default_rng(SEED)
    a = df.loc[df.version == "gate_30", col].astype(int).values
    b = df.loc[df.version == "gate_40", col].astype(int).values
    diffs = [rng.choice(b, len(b)).mean() - rng.choice(a, len(a)).mean() for _ in range(N_BOOT)]
    lo95, hi95 = np.percentile(diffs, [2.5, 97.5])
    lo975, hi975 = np.percentile(diffs, [1.25, 98.75])

    significant = p_value < ALPHA and not (lo975 <= 0 <= hi975)
    results.append({
        "indicator": indicator,
        "retention_gate_30": rate["gate_30"],
        "retention_gate_40": rate["gate_40"],
        "difference_points": 100 * (rate["gate_40"] - rate["gate_30"]),
        "p_value": p_value,
        "boot_ci95_low_points": 100 * lo95, "boot_ci95_high_points": 100 * hi95,
        "boot_ci975_low_points": 100 * lo975, "boot_ci975_high_points": 100 * hi975,
        "conclusion": "gate_40 retains less (significant)" if significant else "Inconclusive",
    })
save(pd.DataFrame(results), "ab_test_results.csv")

# ------------------------------------------------------------ 4. engagement funnel
funnel = con.sql("""
    SELECT CASE
             WHEN sum_gamerounds = 0   THEN '0 rounds'
             WHEN sum_gamerounds <= 5  THEN '1-5'
             WHEN sum_gamerounds <= 20 THEN '6-20'
             WHEN sum_gamerounds <= 50 THEN '21-50'
             ELSE '50+'
           END AS band,
           MIN(sum_gamerounds)       AS lower_bound,
           COUNT(*)                  AS players,
           AVG(retention_7::INT)     AS retention_j7
    FROM cookie_cats
    GROUP BY band
    ORDER BY lower_bound
""").df()
funnel.insert(0, "sort_order", range(1, len(funnel) + 1))
save(funnel.drop(columns="lower_bound"), "engagement_funnel.csv")

# ------------------------------------------------------------ 5. player segments
gb = con.sql("SELECT * FROM gaming_behavior").df()
variables = ["SessionsPerWeek", "AvgSessionDurationMinutes", "PlayerLevel", "InGamePurchases"]
X = gb[variables].dropna()
model = KMeans(n_clusters=3, n_init=10, random_state=SEED).fit(StandardScaler().fit_transform(X))
seg = gb.loc[X.index].copy()
seg["cluster"] = model.labels_

means = seg.groupby("cluster")[variables].mean()
payer = means["InGamePurchases"].idxmax()
others = means.drop(index=payer)["SessionsPerWeek"]
names = {payer: "Payers",
         others.idxmax(): "Highly active non-payers",
         others.idxmin(): "Low-activity non-payers"}
actions = {"Payers": "Retain: loyalty perks",
           "Highly active non-payers": "Convert: entry-level offer",
           "Low-activity non-payers": "Re-engage: reminders and events"}
seg["segment"] = seg["cluster"].map(names)

out = seg.groupby("segment").agg(
    players=("PlayerID", "count"),
    sessions_per_week=("SessionsPerWeek", "mean"),
    avg_session_minutes=("AvgSessionDurationMinutes", "mean"),
    player_level=("PlayerLevel", "mean"),
    payer_share=("InGamePurchases", "mean"),
    high_engagement_share=("EngagementLevel", lambda s: (s == "High").mean()),
).reset_index()
out["share_of_players"] = out["players"] / out["players"].sum()
out["suggested_action"] = out["segment"].map(actions)   # hypothesis, not tested
order = {"Highly active non-payers": 1, "Low-activity non-payers": 2, "Payers": 3}
out = out.sort_values("segment", key=lambda s: s.map(order)).reset_index(drop=True)
save(out.round(4), "segments.csv")

con.close()
print("\nDone. Files written to", OUT.resolve())
