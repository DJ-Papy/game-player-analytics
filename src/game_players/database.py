"""DuckDB database built from the two raw CSV files."""
import duckdb
import pandas as pd

from . import config

TABLES = {"cookie_cats": "userid", "gaming_behavior": "PlayerID"}


def build_database(db_path=config.DATABASE, cookie_cats=config.COOKIE_CATS_CSV, behaviour=config.BEHAVIOUR_CSV):
    """Load both CSV files into db_path and return the table checks. The connection is closed at
    the end, so that the notebooks can open the file in read-only mode."""
    for path in (cookie_cats, behaviour):
        if not path.exists():
            raise FileNotFoundError(f"{path} is missing. See data/README.md for the download link.")
    con = duckdb.connect(str(db_path))
    try:
        con.execute(f"CREATE OR REPLACE TABLE cookie_cats AS SELECT * FROM read_csv_auto('{cookie_cats}')")
        con.execute(f"CREATE OR REPLACE TABLE gaming_behavior AS SELECT * FROM read_csv_auto('{behaviour}')")
        return check_tables(con)
    finally:
        con.close()


def check_tables(con):
    """One row per table: rows, distinct player ids, status ('ok' when one row per player)."""
    rows = []
    for table, key in TABLES.items():
        n, distinct = con.execute(f"SELECT COUNT(*), COUNT(DISTINCT {key}) FROM {table}").fetchall()[0]
        rows.append(dict(table=table, rows=n, distinct_players=distinct, status="ok" if n == distinct else "error"))
    return pd.DataFrame(rows)


def connect(db_path=config.DATABASE):
    """Read-only connection to the database (build it first with `python -m game_players build`)."""
    if not db_path.exists():
        raise FileNotFoundError(f"{db_path} does not exist: run `python -m game_players build` first.")
    return duckdb.connect(str(db_path), read_only=True)


def run_sql(con, file_name):
    """Run one query of sql/ and return it as a DataFrame."""
    return con.execute((config.SQL_DIR / file_name).read_text(encoding="utf-8")).df()
