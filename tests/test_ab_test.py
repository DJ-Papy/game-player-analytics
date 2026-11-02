import pytest

from game_players import ab_test

from .conftest import cookie_cats_like

# Published counts of the Cookie Cats test: gate_30 then gate_40
PLAYERS = [44700, 45489]
RETAINED_D1 = [20034, 20119]
RETAINED_D7 = [8502, 8279]


def test_published_p_values():
    assert ab_test.ztest_pvalue(RETAINED_D7, PLAYERS) == pytest.approx(0.0016, abs=1e-4)
    assert ab_test.ztest_pvalue(RETAINED_D1, PLAYERS) == pytest.approx(0.0744, abs=1e-4)


def test_published_sample_ratio_mismatch():
    assert ab_test.srm_pvalue(PLAYERS) == pytest.approx(0.0086, abs=1e-4)


def test_wilson_interval_of_gate_30_d7():
    low, high = ab_test.wilson(8502, 44700)
    assert (round(100 * low, 2), round(100 * high, 2)) == (18.66, 19.39)


def test_bootstrap_is_reproducible():
    a, b = [0, 1, 1, 0, 1] * 20, [0, 0, 1, 0, 1] * 20
    first = ab_test.bootstrap_diff(a, b, n_boot=200, seed=42)
    assert (first == ab_test.bootstrap_diff(a, b, n_boot=200, seed=42)).all()


def test_decision_rule():
    df = cookie_cats_like(n=2000)
    result = ab_test.compare_retention(df, n_boot=300).set_index("indicator")
    for row in result.itertuples():
        inside = row.boot_ci975_low_points <= 0 <= row.boot_ci975_high_points
        significant = row.p_value < 0.025 and not inside
        assert (row.conclusion != "Inconclusive") == significant


def test_retention_by_version_rows():
    out = ab_test.retention_by_version(cookie_cats_like(n=1000))
    assert out[["indicator", "version"]].values.tolist() == [
        ["Day 1", "gate_30"], ["Day 7", "gate_30"], ["Day 1", "gate_40"], ["Day 7", "gate_40"]]
    assert ((out["ci_low"] <= out["retention"]) & (out["retention"] <= out["ci_high"])).all()
