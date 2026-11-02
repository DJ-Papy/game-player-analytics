import random

import pandas as pd
import pytest

from game_players import config


def cookie_cats_like(n=4000, seed=3):
    """Random players with the columns of cookie_cats.csv (the real file is not redistributed)."""
    rng = random.Random(seed)
    rows = []
    for i in range(n):
        version = "gate_30" if i % 2 else "gate_40"
        rounds = int(rng.expovariate(1 / 50))
        d1 = rng.random() < 0.45
        d7 = rng.random() < (0.05 + min(rounds, 200) / 400)
        rows.append(dict(userid=1000 + i, version=version, sum_gamerounds=rounds, retention_1=d1, retention_7=d7))
    return pd.DataFrame(rows)


@pytest.fixture(scope="session")
def cookie_cats_csv(tmp_path_factory):
    path = tmp_path_factory.mktemp("raw") / "cookie_cats.csv"
    cookie_cats_like().to_csv(path, index=False)
    return path


@pytest.fixture(scope="session")
def behaviour():
    """The behaviour dataset is committed (MIT licence): tests run on the real file."""
    return pd.read_csv(config.BEHAVIOUR_CSV)
