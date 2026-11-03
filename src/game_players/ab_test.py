"""A/B test of the first gate (gate_30 vs gate_40) on D1 and D7 retention."""
import numpy as np
import pandas as pd
from scipy.stats import chisquare
from statsmodels.stats.proportion import proportion_confint, proportions_ztest

from . import config

CONTROL, TREATMENT = "gate_30", "gate_40"
METRICS = {"Day 1": "retention_1", "Day 7": "retention_7"}


def srm_pvalue(group_sizes):
    """Sample ratio mismatch: chi-square test against an equal split. A small value means
    the assignment should be checked before trusting the test."""
    return float(chisquare(list(group_sizes)).pvalue)


def wilson(successes, trials):
    """95% Wilson interval of a proportion (as fractions)."""
    return proportion_confint(successes, trials, method="wilson")


def ztest_pvalue(successes, trials):
    """Two-sided two-proportion z-test."""
    return float(proportions_ztest(list(successes), list(trials))[1])


def bootstrap_diff(control, treatment, n_boot=config.N_BOOT, seed=config.SEED):
    """Bootstrap distribution of mean(treatment) - mean(control), resampling players."""
    rng = np.random.default_rng(seed)
    return np.array([rng.choice(treatment, len(treatment)).mean() - rng.choice(control, len(control)).mean()
                     for _ in range(n_boot)])


def retention_by_version(df):
    """Retention of each version with its Wilson interval, one row per indicator and version."""
    rows = []
    for version, g in df.groupby("version"):
        for indicator, col in METRICS.items():
            successes, n = int(g[col].sum()), len(g)
            low, high = wilson(successes, n)
            rows.append(dict(indicator=indicator, version=version, players=n,
                             retention=successes / n, ci_low=low, ci_high=high))
    return pd.DataFrame(rows)


def compare_retention(df, alpha=config.ALPHA, n_boot=config.N_BOOT, seed=config.SEED):
    """z-test and bootstrap (95% and 1 - alpha intervals) of gate_40 - gate_30, per indicator.
    A difference is significant if p < alpha and the 1 - alpha bootstrap interval excludes 0."""
    tail = 100 * alpha / 2
    rows = []
    for indicator, col in METRICS.items():
        g = df.groupby("version")[col].agg(["sum", "count"])
        p_value = ztest_pvalue(g["sum"].values, g["count"].values)
        rate = g["sum"] / g["count"]
        diffs = bootstrap_diff(df.loc[df.version == CONTROL, col].astype(int).values,
                               df.loc[df.version == TREATMENT, col].astype(int).values, n_boot, seed)
        lo95, hi95 = np.percentile(diffs, [2.5, 97.5])
        lo_a, hi_a = np.percentile(diffs, [tail, 100 - tail])
        significant = p_value < alpha and not (lo_a <= 0 <= hi_a)
        rows.append({
            "indicator": indicator,
            "retention_gate_30": rate[CONTROL],
            "retention_gate_40": rate[TREATMENT],
            "difference_points": 100 * (rate[TREATMENT] - rate[CONTROL]),
            "p_value": p_value,
            "boot_ci95_low_points": 100 * lo95, "boot_ci95_high_points": 100 * hi95,
            "boot_ci975_low_points": 100 * lo_a, "boot_ci975_high_points": 100 * hi_a,
            "conclusion": "gate_40 retains less (significant)" if significant and rate[TREATMENT] < rate[CONTROL]
            else "gate_40 retains more (significant)" if significant else "Inconclusive",
        })
    return pd.DataFrame(rows)
