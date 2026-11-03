"""Tables read by the Power BI dashboard (dashboard/data/*.csv).

Separator ';' and decimal ',' (French Power BI / Excel). Column names are part of the contract
with dashboard/game-player-analytics.pbix: renaming one breaks the report.
"""
from . import ab_test, config, segmentation
from .database import run_sql


def _save(df, out_dir, name):
    df.to_csv(out_dir / name, sep=";", decimal=",", index=False, encoding="utf-8")
    print(f"  {name}: {len(df)} row(s)")


def export_dashboard(con, out_dir=config.DASHBOARD_DATA):
    out_dir.mkdir(parents=True, exist_ok=True)

    kpi = run_sql(con, "01_kpis.sql")
    _save(kpi[["players", "retention_d1"]].assign(retention_j7=kpi["retention_d7"])
          .rename(columns={"retention_d1": "retention_j1"}), out_dir, "kpi_global.csv")

    players = con.execute("SELECT version, retention_1, retention_7 FROM cookie_cats").df()
    _save(ab_test.retention_by_version(players), out_dir, "retention_by_version.csv")
    _save(ab_test.compare_retention(players), out_dir, "ab_test_results.csv")

    bands = run_sql(con, "03_engagement_bands.sql")
    _save(bands[["sort_order", "band", "players", "retention_d7"]].rename(columns={"retention_d7": "retention_j7"}),
          out_dir, "engagement_funnel.csv")

    behaviour = con.execute("SELECT * FROM gaming_behavior").df()
    profile = segmentation.segment_profile(segmentation.fit_segments(behaviour))
    _save(profile.round(4), out_dir, "segments.csv")
