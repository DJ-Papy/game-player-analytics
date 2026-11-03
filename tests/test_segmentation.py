import pandas as pd
import pytest

from game_players import config, segmentation


@pytest.fixture(scope="module")
def profile(behaviour):
    return segmentation.segment_profile(segmentation.fit_segments(behaviour))


def test_published_segments_are_reproduced(profile):
    published = pd.read_csv(config.DASHBOARD_DATA / "segments.csv", sep=";", decimal=",")
    assert profile["segment"].tolist() == published["segment"].tolist()
    assert profile["share_of_players"].round(3).tolist() == pytest.approx(
        published["share_of_players"].round(3).tolist(), abs=0.005)


def test_payers_segment_is_the_payers(profile):
    payers = profile.set_index("segment").loc["Payers"]
    assert payers["payer_share"] == 1.0


def test_no_more_structure_than_shuffled_data(behaviour):
    X, _ = segmentation.standardize(behaviour, config.SEGMENT_VARIABLES)
    check = segmentation.structure_check(X, ks=[3]).iloc[0]
    assert abs(check["silhouette_real"] - check["silhouette_shuffled"]) < 0.01
