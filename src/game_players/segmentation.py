"""Player segmentation (K-means) with a check that the segments are more than noise.

The check compares the silhouette on the real data with the silhouette on the same data whose
columns were shuffled independently (no relation between variables by construction), and the
stability of the clusters across random seeds (adjusted Rand index).
"""
import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.metrics import adjusted_rand_score, silhouette_score
from sklearn.preprocessing import StandardScaler

from . import config

SILHOUETTE_SAMPLE = 10_000
ACTIONS = {"Payers": "Retain: loyalty perks",
           "Highly active non-payers": "Convert: entry-level offer",
           "Low-activity non-payers": "Re-engage: reminders and events"}   # hypotheses, not tested


def standardize(df, variables):
    """Standardised matrix of `variables` (rows with a missing value dropped) and the rows kept."""
    rows = df[variables].dropna()
    return StandardScaler().fit_transform(rows), rows.index


def kmeans(X, k, seed=config.SEED):
    return KMeans(n_clusters=k, n_init=10, random_state=seed).fit(X)


def silhouette(X, labels):
    return silhouette_score(X, labels, sample_size=SILHOUETTE_SAMPLE, random_state=config.SEED)


def shuffle_columns(X, seed=0):
    rng = np.random.default_rng(seed)
    return np.column_stack([rng.permutation(X[:, i]) for i in range(X.shape[1])])


def scan(X, ks=range(2, 8)):
    """Inertia and silhouette for each k."""
    rows = []
    for k in ks:
        model = kmeans(X, k)
        rows.append(dict(k=k, inertia=round(model.inertia_), silhouette=round(silhouette(X, model.labels_), 3)))
    return pd.DataFrame(rows)


def structure_check(X, ks=range(2, 7), seeds=(config.SEED, 7)):
    """Silhouette on real vs shuffled data, and agreement of two seeds (ARI), for each k."""
    X_shuffled = shuffle_columns(X)
    rows = []
    for k in ks:
        real, other = kmeans(X, k, seeds[0]), kmeans(X, k, seeds[1])
        noise = kmeans(X_shuffled, k, seeds[0])
        rows.append(dict(k=k,
                         silhouette_real=round(silhouette(X, real.labels_), 3),
                         silhouette_shuffled=round(silhouette(X_shuffled, noise.labels_), 3),
                         ari_between_seeds=round(adjusted_rand_score(real.labels_, other.labels_), 3)))
    return pd.DataFrame(rows)


def fit_segments(df, variables=config.SEGMENT_VARIABLES, k=config.N_SEGMENTS):
    """K-means segments, named from their averages: the payers' cluster first, then the
    non-payers ranked by sessions per week. Returns the rows used, with `cluster` and `segment`."""
    X, index = standardize(df, variables)
    seg = df.loc[index].copy()
    seg["cluster"] = kmeans(X, k).labels_
    means = seg.groupby("cluster")[variables].mean()
    payers = means["InGamePurchases"].idxmax()
    others = means.drop(index=payers)["SessionsPerWeek"]
    names = {payers: "Payers", others.idxmax(): "Highly active non-payers", others.idxmin(): "Low-activity non-payers"}
    seg["segment"] = seg["cluster"].map(names)
    return seg


def segment_profile(seg):
    """One row per segment: size, averages, payer and high-engagement shares, suggested action."""
    out = seg.groupby("segment").agg(
        players=("PlayerID", "count"),
        sessions_per_week=("SessionsPerWeek", "mean"),
        avg_session_minutes=("AvgSessionDurationMinutes", "mean"),
        player_level=("PlayerLevel", "mean"),
        payer_share=("InGamePurchases", "mean"),
        high_engagement_share=("EngagementLevel", lambda s: (s == "High").mean()),
    ).reset_index()
    out["share_of_players"] = out["players"] / out["players"].sum()
    out["suggested_action"] = out["segment"].map(ACTIONS)
    order = {"Highly active non-payers": 1, "Low-activity non-payers": 2, "Payers": 3}
    return out.sort_values("segment", key=lambda s: s.map(order)).reset_index(drop=True)
