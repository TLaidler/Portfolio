"""Clustered feature importance (AFML Ch. 6 + MLAM Ch. 4).

Correlated features cause substitution effects: importance is diluted among
near-duplicates and the resulting ranking is unstable. López de Prado's
remedy is:
  1. Cluster features on the denoised correlation distance with Optimal
     Number of Clusters (ONC, silhouette maximisation).
  2. Compute Mean Decrease Impurity / Accuracy at the *cluster* level,
     aggregating members of each cluster before fitting.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Tuple

import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import log_loss
from sklearn.model_selection import KFold
from sklearn.preprocessing import StandardScaler

from .denoising import corr_to_dist, denoise_corr


# --------------------------------------------------------------------------
# ONC — Optimal Number of Clusters (simplified hierarchical KMeans variant)
# --------------------------------------------------------------------------

def _silhouette_scores(X: np.ndarray, labels: np.ndarray) -> np.ndarray:
    from sklearn.metrics import silhouette_samples
    if len(np.unique(labels)) < 2:
        return np.zeros(len(labels))
    return silhouette_samples(X, labels)


def onc_clustering(
    corr: pd.DataFrame,
    max_clusters: int | None = None,
    n_init: int = 10,
    random_state: int = 0,
) -> Dict[int, List[str]]:
    """Optimal Number of Clusters via silhouette maximisation.

    Clusters the *distance* matrix with KMeans for k in [2, max_clusters] and
    keeps the k maximising the silhouette t-statistic.
    """
    dist = corr_to_dist(corr).to_numpy()
    n = dist.shape[0]
    max_k = max_clusters or max(2, n // 2)

    best_k, best_score, best_labels = 2, -np.inf, None
    for k in range(2, min(max_k, n - 1) + 1):
        km = KMeans(n_clusters=k, n_init=n_init, random_state=random_state)
        labels = km.fit_predict(dist)
        s = _silhouette_scores(dist, labels)
        score = s.mean() / (s.std() + 1e-9)  # silhouette t-stat
        if score > best_score:
            best_score, best_k, best_labels = score, k, labels

    clusters: Dict[int, List[str]] = {c: [] for c in range(best_k)}
    for feat, lab in zip(corr.columns, best_labels):
        clusters[int(lab)].append(feat)
    return clusters


# --------------------------------------------------------------------------
# Cluster aggregation: mean of Z-scored features within each cluster
# --------------------------------------------------------------------------

def cluster_representatives(
    X: pd.DataFrame, clusters: Dict[int, List[str]]
) -> pd.DataFrame:
    """Replace each cluster with the mean of its standardized members."""
    Xz = pd.DataFrame(
        StandardScaler().fit_transform(X.fillna(0.0)),
        index=X.index, columns=X.columns,
    )
    reps: Dict[str, pd.Series] = {}
    for c, members in clusters.items():
        reps[f"cluster_{c}"] = Xz[members].mean(axis=1)
    return pd.concat(reps, axis=1)


# --------------------------------------------------------------------------
# Clustered MDI / MDA
# --------------------------------------------------------------------------

@dataclass
class ImportanceResult:
    mdi: pd.Series
    mda: pd.Series
    clusters: Dict[int, List[str]]


def clustered_mdi(
    X: pd.DataFrame,
    y: pd.Series,
    clusters: Dict[int, List[str]],
    sample_weight: np.ndarray | None = None,
    n_estimators: int = 200,
    random_state: int = 0,
) -> pd.Series:
    """Mean Decrease Impurity computed on cluster-aggregated features."""
    Xc = cluster_representatives(X, clusters)
    rf = RandomForestClassifier(
        n_estimators=n_estimators,
        max_features=1,
        oob_score=False,
        random_state=random_state,
        n_jobs=-1,
    )
    rf.fit(Xc.fillna(0.0), y, sample_weight=sample_weight)
    imp = pd.Series(rf.feature_importances_, index=Xc.columns).sort_values(ascending=False)
    return imp


def clustered_mda(
    X: pd.DataFrame,
    y: pd.Series,
    clusters: Dict[int, List[str]],
    sample_weight: np.ndarray | None = None,
    n_splits: int = 5,
    n_estimators: int = 100,
    random_state: int = 0,
) -> pd.Series:
    """Mean Decrease Accuracy at the cluster level.

    For each cluster, shuffle all its member features jointly in the test
    fold and measure the increase in log-loss vs. the unshuffled baseline.
    """
    kf = KFold(n_splits=n_splits)
    results = {c: [] for c in clusters}
    base_scores: List[float] = []
    rng = np.random.default_rng(random_state)

    Xa = X.fillna(0.0).reset_index(drop=True)
    y = y.reset_index(drop=True)
    sw = pd.Series(sample_weight) if sample_weight is not None else None

    for train_idx, test_idx in kf.split(Xa):
        Xtr, ytr = Xa.iloc[train_idx], y.iloc[train_idx]
        Xte, yte = Xa.iloc[test_idx], y.iloc[test_idx]
        sw_tr = sw.iloc[train_idx].to_numpy() if sw is not None else None

        rf = RandomForestClassifier(
            n_estimators=n_estimators, random_state=random_state, n_jobs=-1
        )
        rf.fit(Xtr, ytr, sample_weight=sw_tr)
        proba = rf.predict_proba(Xte)
        base = -log_loss(yte, proba, labels=rf.classes_)
        base_scores.append(base)

        for c, members in clusters.items():
            Xte_shuf = Xte.copy()
            perm = rng.permutation(len(Xte_shuf))
            for m in members:
                Xte_shuf[m] = Xte_shuf[m].to_numpy()[perm]
            proba_s = rf.predict_proba(Xte_shuf)
            shuf = -log_loss(yte, proba_s, labels=rf.classes_)
            results[c].append(base - shuf)  # positive = cluster was useful

    mda = pd.Series(
        {f"cluster_{c}": float(np.mean(v)) for c, v in results.items()}
    ).sort_values(ascending=False)
    return mda


def run_clustered_importance(
    X: pd.DataFrame,
    y: pd.Series,
    sample_weight: np.ndarray | None = None,
    random_state: int = 0,
) -> ImportanceResult:
    # Denoise the correlation before clustering
    corr = X.corr().fillna(0.0)
    q = max(1.01, X.shape[0] / max(1, X.shape[1]))
    corr_dn = denoise_corr(corr, q=q)
    clusters = onc_clustering(corr_dn, random_state=random_state)
    mdi = clustered_mdi(X, y, clusters, sample_weight, random_state=random_state)
    mda = clustered_mda(X, y, clusters, sample_weight, random_state=random_state)
    return ImportanceResult(mdi=mdi, mda=mda, clusters=clusters)
