"""Project settings: file locations and the parameters of the statistical tests."""
import os
from pathlib import Path

ROOT = Path(os.environ.get("GAME_PLAYERS_ROOT", Path(__file__).resolve().parents[2]))

COOKIE_CATS_CSV = ROOT / "data" / "raw" / "cookie_cats.csv"
BEHAVIOUR_CSV = ROOT / "data" / "raw" / "online_gaming_behavior_insights.csv"
DATABASE = ROOT / "game.duckdb"
SQL_DIR = ROOT / "sql"
DASHBOARD_DATA = ROOT / "dashboard" / "data"

# A/B test. Two retention indicators (D1, D7) are tested: Bonferroni threshold 0.05 / 2.
ALPHA = 0.025
N_BOOT = 5000
SEED = 42

# Segmentation: one variable per behaviour (frequency, length, progression, payment).
# PlayTimeHours and AchievementsUnlocked would count overall activity twice.
SEGMENT_VARIABLES = ["SessionsPerWeek", "AvgSessionDurationMinutes", "PlayerLevel", "InGamePurchases"]
N_SEGMENTS = 3
