"""Purged K-Fold and Combinatorial Purged CV (AFML Ch. 7).

Standard K-Fold leaks information in time-series ML: a test sample's label
may depend on bars that also appear in the training set. We fix this with:
  - Purging: remove from training any sample whose evaluation window
    overlaps the test fold.
  - Embargo: drop a buffer period right after each test fold so that serial
    correlation near the test boundary does not contaminate training.
  - CPCV: split the time line into N groups, train/test on every
    k-combination of them — generating many near-independent backtest paths.
"""
from __future__ import annotations

from itertools import combinations
from typing import Iterable, List, Tuple

import numpy as np
import pandas as pd
from sklearn.model_selection._split import _BaseKFold


def _purge_train(
    train_times: pd.Series, test_times: pd.Series
) -> pd.Series:
    """Drop train samples whose label horizon overlaps any test sample.

    train_times and test_times are Series: index = t0 (label start),
    values = t1 (label end).
    """
    trn = train_times.copy()
    for t0, t1 in test_times.items():
        # Drop train labels that started before t1 AND ended after t0
        overlap = (trn.index <= t1) & (trn >= t0)
        trn = trn[~overlap]
    return trn


def _embargo(
    times: pd.Series, test_times: pd.Series, pct: float
) -> pd.Series:
    if pct <= 0:
        return times
    n_embargo = int(pct * len(times))
    if n_embargo == 0:
        return times
    blocked = pd.DatetimeIndex([])
    for end in test_times.values:
        after = times.index[times.index > end][:n_embargo]
        blocked = blocked.append(after)
    return times.drop(blocked, errors="ignore")


class PurgedKFold(_BaseKFold):
    """K-Fold that purges and embargoes using label lifetimes t1."""

    def __init__(self, n_splits: int = 5, t1: pd.Series | None = None, embargo_pct: float = 0.01):
        super().__init__(n_splits, shuffle=False, random_state=None)
        self.t1 = t1
        self.embargo_pct = embargo_pct

    def split(self, X, y=None, groups=None):
        if self.t1 is None:
            raise ValueError("t1 must be provided")
        indices = np.arange(len(X))
        test_ranges = np.array_split(indices, self.n_splits)

        for test_idx in test_ranges:
            t0_test = X.index[test_idx[0]]
            t1_test = self.t1.iloc[test_idx].max()

            train_times = self.t1.drop(X.index[test_idx])
            mask_overlap = (train_times.index <= t1_test) & (train_times >= t0_test)
            train_times = train_times[~mask_overlap]

            # Embargo after test set
            n_emb = int(self.embargo_pct * len(X))
            if n_emb > 0:
                emb_end = min(test_idx[-1] + n_emb, len(X) - 1)
                emb_idx = X.index[test_idx[-1] + 1: emb_end + 1]
                train_times = train_times.drop(emb_idx, errors="ignore")

            train_idx = np.where(X.index.isin(train_times.index))[0]
            yield train_idx, test_idx


# --------------------------------------------------------------------------
# Combinatorial Purged CV (AFML 12.4)
# --------------------------------------------------------------------------

def combinatorial_splits(n_groups: int, n_test_groups: int) -> List[Tuple[int, ...]]:
    return list(combinations(range(n_groups), n_test_groups))


class CombinatorialPurgedCV:
    """Generates (train, test_groups) index lists for CPCV.

    The full time series is partitioned into `n_groups`. Each "split" picks
    `k = n_test_groups` of them as test. With N groups and k test, you get
    C(N, k) splits, producing (N-1 choose k-1) paths per group. López de Prado
    recommends values such as N=6, k=2 → 15 splits, 5 paths per group.
    """

    def __init__(
        self,
        n_groups: int = 6,
        n_test_groups: int = 2,
        t1: pd.Series | None = None,
        embargo_pct: float = 0.01,
    ):
        self.n_groups = n_groups
        self.n_test_groups = n_test_groups
        self.t1 = t1
        self.embargo_pct = embargo_pct

    def split_indices(self, index: pd.DatetimeIndex) -> List[Tuple[np.ndarray, np.ndarray, Tuple[int, ...]]]:
        if self.t1 is None:
            raise ValueError("t1 required")
        n = len(index)
        bounds = np.linspace(0, n, self.n_groups + 1, dtype=int)
        groups = [np.arange(bounds[i], bounds[i + 1]) for i in range(self.n_groups)]

        out = []
        n_emb = int(self.embargo_pct * n)
        for combo in combinatorial_splits(self.n_groups, self.n_test_groups):
            test_idx = np.sort(np.concatenate([groups[g] for g in combo]))
            all_idx = np.arange(n)
            train_mask = np.ones(n, dtype=bool)
            train_mask[test_idx] = False

            # Purge against each contiguous test group separately
            for g in combo:
                g_idx = groups[g]
                t0_g = index[g_idx[0]]
                t1_g = self.t1.iloc[g_idx].max()
                # Drop train samples whose label lifetime overlaps [t0_g, t1_g]
                train_t1 = self.t1
                overlap = (train_t1.index <= t1_g) & (train_t1 >= t0_g)
                train_mask &= ~overlap.values
                # Embargo after the test group
                emb_end = min(g_idx[-1] + 1 + n_emb, n)
                train_mask[g_idx[-1] + 1: emb_end] = False

            train_idx = all_idx[train_mask]
            out.append((train_idx, test_idx, combo))
        return out
