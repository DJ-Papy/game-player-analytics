"""Command line entry point.

    python -m game_players build   load the CSV files into game.duckdb, check them, export the dashboard tables
"""
import argparse
import sys
from pathlib import Path

from . import config
from .database import build_database, connect
from .export import export_dashboard


def main(argv=None):
    parser = argparse.ArgumentParser(prog="python -m game_players", description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("command", choices=["build"])
    parser.add_argument("--cookie-cats", type=Path, default=config.COOKIE_CATS_CSV)
    parser.add_argument("--behaviour", type=Path, default=config.BEHAVIOUR_CSV)
    parser.add_argument("--db", type=Path, default=config.DATABASE)
    parser.add_argument("--out", type=Path, default=config.DASHBOARD_DATA)
    args = parser.parse_args(argv)

    checks = build_database(args.db, args.cookie_cats, args.behaviour)
    print(checks.to_string(index=False))
    if (checks["status"] != "ok").any():
        print("Data checks failed: nothing exported.", file=sys.stderr)
        return 1
    con = connect(args.db)
    try:
        print("Exporting dashboard tables:")
        export_dashboard(con, args.out)
    finally:
        con.close()
    print("Done:", args.out.resolve())
    return 0


if __name__ == "__main__":
    sys.exit(main())
