import pandas as pd
import pytest

from game_players import config
from game_players.__main__ import main
from game_players.database import build_database

# Columns read by dashboard/game-player-analytics.pbix: renaming or reordering them breaks the report.
DASHBOARD_CONTRACT = {
    "kpi_global.csv": ["players", "retention_j1", "retention_j7"],
    "retention_by_version.csv": ["indicator", "version", "players", "retention", "ci_low", "ci_high"],
    "ab_test_results.csv": ["indicator", "retention_gate_30", "retention_gate_40", "difference_points", "p_value",
                            "boot_ci95_low_points", "boot_ci95_high_points", "boot_ci975_low_points",
                            "boot_ci975_high_points", "conclusion"],
    "engagement_funnel.csv": ["sort_order", "band", "players", "retention_j7"],
    "segments.csv": ["segment", "players", "sessions_per_week", "avg_session_minutes", "player_level", "payer_share",
                     "high_engagement_share", "share_of_players", "suggested_action"],
}


@pytest.fixture(scope="module")
def exported(cookie_cats_csv, tmp_path_factory):
    folder = tmp_path_factory.mktemp("build")
    out = folder / "dashboard"
    code = main(["build", "--cookie-cats", str(cookie_cats_csv), "--behaviour", str(config.BEHAVIOUR_CSV),
                 "--db", str(folder / "game.duckdb"), "--out", str(out)])
    assert code == 0
    return out


@pytest.mark.parametrize("name", sorted(DASHBOARD_CONTRACT))
def test_dashboard_contract(exported, name):
    df = pd.read_csv(exported / name, sep=";", decimal=",")
    assert df.columns.tolist() == DASHBOARD_CONTRACT[name]


def test_engagement_bands_in_order(exported):
    bands = pd.read_csv(exported / "engagement_funnel.csv", sep=";", decimal=",")
    assert bands["band"].tolist() == ["0 rounds", "1-5", "6-20", "21-50", "50+"]


def test_duplicate_player_ids_are_reported(tmp_path, cookie_cats_csv):
    df = pd.read_csv(cookie_cats_csv)
    pd.concat([df, df.head(1)]).to_csv(tmp_path / "dup.csv", index=False)
    checks = build_database(tmp_path / "db.duckdb", tmp_path / "dup.csv", config.BEHAVIOUR_CSV)
    assert checks.set_index("table").loc["cookie_cats", "status"] == "error"


def test_missing_file_gives_a_clear_error(tmp_path):
    with pytest.raises(FileNotFoundError, match="data/README.md"):
        build_database(tmp_path / "db.duckdb", tmp_path / "missing.csv", config.BEHAVIOUR_CSV)
