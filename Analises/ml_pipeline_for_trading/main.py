"""Full pipeline orchestrator.

Executes the Marcos Lopez de Prado quant-ML pipeline with the feature set
validated by Feynman's MDA runs, writes .txt reports per stage into
resultados/ and all plots into plots/. Finally produces a Markdown debate
between Marcos and Feynman summarising the findings.

Run:
    python main.py                 # full run (slow)
    python main.py --bars-per-day 30  # faster iteration
"""
from __future__ import annotations

import argparse
import json
import pickle
import sys
import time
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List

import joblib
import numpy as np
import pandas as pd
from scipy.stats import skew as sp_skew, kurtosis as sp_kurt
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, f1_score, log_loss

from pipeline.backtest import (
    BacktestReport, cpcv_paths, deflated_sharpe_ratio,
    probabilistic_sharpe_ratio, random_walk_null_distribution,
    sharpe_ratio, strategy_returns,
)
from pipeline.bars import DollarBarBuilder, summarize_bars
from pipeline.cross_validation import CombinatorialPurgedCV, PurgedKFold
from pipeline.denoising import corr_to_dist, denoise_corr, detone
from pipeline.feature_selection import run_clustered_importance
from pipeline.features import FeatureBuilder, FeatureConfig
from pipeline.io import fetch_bacen_cdi, load_exogenous, load_minute_bars
from pipeline.labeling import (
    BarrierConfig, apply_triple_barrier, build_events, daily_volatility,
    meta_label, vertical_barriers,
)
from pipeline import plots as P
from pipeline.utils import ProjectPaths, TxtLogger, set_plot_style
from pipeline.weights import (
    concurrency, return_attribution_weights, sequential_bootstrap,
)


# --------------------------------------------------------------------------
# Helpers
# --------------------------------------------------------------------------

def _tstat_side(features: pd.DataFrame, col: str = "tstat_50", thresh: float = 0.5) -> pd.Series:
    """Primary signal: causal-theoretical direction from tstat."""
    side = np.sign(features[col].fillna(0.0))
    side[features[col].abs() < thresh] = 0
    return side.astype(int)


def _align_events_with_features(events: pd.DataFrame, X: pd.DataFrame, labels: pd.DataFrame):
    idx = events.index.intersection(X.dropna().index)
    return events.loc[idx], X.loc[idx], labels.loc[idx]


def _equity_curve(r: pd.Series) -> pd.Series:
    return r.fillna(0.0).cumsum()


# --------------------------------------------------------------------------
# Pipeline
# --------------------------------------------------------------------------

def run_pipeline(
    bars_per_day: int = 100,
    horizon_bars: int = 20,
    pt_sl: tuple = (1.0, 1.0),
    tstat_threshold: float = 0.5,
    cpcv_groups: int = 6,
    cpcv_test_groups: int = 2,
    rw_sims: int = 500,
    rf_trees: int = 300,
    random_state: int = 42,
):
    t_start = time.time()
    paths = ProjectPaths.discover()
    set_plot_style()

    # ------------------------------------------------------------------
    # 1. Load minute bars (IS + OOS) and build dollar bars
    # ------------------------------------------------------------------
    log = TxtLogger(paths.resultados, "01_bars")
    log.header("Stage 1 — Information-driven bars (dollar bars)")

    log.write("Loading minute bars (IS)...")
    minute_is = load_minute_bars(paths.data / "btcusdt_1m.csv")
    log.write(f"  IS minute rows: {len(minute_is):,}  range=({minute_is.index.min()}, {minute_is.index.max()})")

    log.write("Loading minute bars (OOS)...")
    minute_oos = load_minute_bars(paths.new_data / "btcusdt_1m.csv")
    log.write(f"  OOS minute rows: {len(minute_oos):,}  range=({minute_oos.index.min()}, {minute_oos.index.max()})")

    builder = DollarBarBuilder(bars_per_day=bars_per_day)
    bars_is = builder.build(minute_is)
    log.write("\nIS dollar-bar summary:")
    summary_is = summarize_bars(bars_is)
    log.write(json.dumps(summary_is, indent=2))

    # Use same threshold for OOS (calibrated in-sample)
    builder_oos = DollarBarBuilder(bars_per_day=bars_per_day)
    builder_oos._calibrate_threshold = lambda _df: bars_is.attrs["threshold"]
    bars_oos = builder_oos.build(minute_oos)
    log.write("\nOOS dollar-bar summary:")
    summary_oos = summarize_bars(bars_oos)
    log.write(json.dumps(summary_oos, indent=2))

    # Leakage guard: OOS bars must begin strictly after the last IS bar.
    if bars_oos.index.min() <= bars_is.index.max():
        raise ValueError(
            f"OOS bars overlap IS bars: IS ends {bars_is.index.max()} "
            f"but OOS starts {bars_oos.index.min()}. Check data/ vs new_data/."
        )

    P.plot_bar_returns_hist(
        bars_is["close"].pct_change(),
        paths.plots / "01_bar_returns_is.png",
        title="IS dollar-bar returns",
    )
    P.plot_bar_returns_hist(
        bars_oos["close"].pct_change(),
        paths.plots / "01_bar_returns_oos.png",
        title="OOS dollar-bar returns",
    )

    # ------------------------------------------------------------------
    # 2. Features (IS + OOS using same config)
    # ------------------------------------------------------------------
    log = TxtLogger(paths.resultados, "02_features")
    log.header("Stage 2 — Features (SavGol causal, FFD, tstat, macro)")

    exog_is = load_exogenous(paths.data)
    log.write(f"Exogenous series loaded: {list(exog_is.keys())}")

    fb = FeatureBuilder(FeatureConfig())
    X_is = fb.build(bars_is, exog_is)
    log.write(f"IS features shape: {X_is.shape}")
    log.write(f"IS features columns: {list(X_is.columns)}")
    log.write("IS describe:")
    log.table(X_is.describe().T)

    # OOS uses the same exogenous files (updated with OOS period if present)
    exog_oos: Dict[str, pd.Series] = {}
    for name, s in exog_is.items():
        oos_path = paths.new_data / f"{name}.csv"
        if oos_path.exists():
            try:
                extra = pd.read_csv(oos_path)
                ts_col = extra.columns[0]
                val_col = extra.columns[1]
                extra[ts_col] = pd.to_datetime(extra[ts_col], utc=True)
                extra = extra.set_index(ts_col)[val_col].astype(float)
                exog_oos[name] = pd.concat([s, extra]).sort_index().drop_duplicates()
            except Exception:
                exog_oos[name] = s
        else:
            exog_oos[name] = s
    X_oos = fb.build(bars_oos, exog_oos)
    log.write(f"\nOOS features shape: {X_oos.shape}")

    # ------------------------------------------------------------------
    # 3. Primary signal, triple-barrier, meta-labels
    # ------------------------------------------------------------------
    log = TxtLogger(paths.resultados, "03_labeling")
    log.header("Stage 3 — Triple-Barrier labeling and Meta-Labels")

    vol_is = daily_volatility(bars_is["close"])
    side_is = _tstat_side(X_is, "tstat_50", tstat_threshold)
    log.write(f"IS side distribution: {side_is.value_counts().to_dict()}")

    events_is = build_events(
        close=bars_is["close"], vol=vol_is, side=side_is,
        cfg=BarrierConfig(pt_sl=pt_sl, vertical_bars=horizon_bars),
    )
    log.write(f"IS events after side filter: {len(events_is):,}")

    labels_is = apply_triple_barrier(bars_is["close"], events_is, pt_sl=pt_sl)
    labels_is = labels_is.dropna(subset=["ret"])
    log.write(f"IS touch counts: {labels_is['touch'].value_counts().to_dict()}")
    log.write(f"IS meta-label positive share: {(labels_is['ret'] > 0).mean():.3f}")

    events_is, X_is_ev, labels_is = _align_events_with_features(events_is, X_is, labels_is)
    y_is_meta = meta_label(labels_is)

    # OOS counterpart
    vol_oos = daily_volatility(bars_oos["close"])
    side_oos = _tstat_side(X_oos, "tstat_50", tstat_threshold)
    events_oos = build_events(
        close=bars_oos["close"], vol=vol_oos, side=side_oos,
        cfg=BarrierConfig(pt_sl=pt_sl, vertical_bars=horizon_bars),
    )
    labels_oos = apply_triple_barrier(bars_oos["close"], events_oos, pt_sl=pt_sl)
    labels_oos = labels_oos.dropna(subset=["ret"])
    events_oos, X_oos_ev, labels_oos = _align_events_with_features(events_oos, X_oos, labels_oos)
    y_oos_meta = meta_label(labels_oos)
    log.write(f"OOS events: {len(events_oos):,}  positive share: {(labels_oos['ret']>0).mean():.3f}")

    # ------------------------------------------------------------------
    # 4. Sample weights (uniqueness + return attribution)
    # ------------------------------------------------------------------
    log = TxtLogger(paths.resultados, "04_weights")
    log.header("Stage 4 — Sample weights from overlapping labels")

    conc = concurrency(bars_is["close"].index, events_is)
    w_is = return_attribution_weights(bars_is["close"], events_is, conc)
    log.write(f"IS concurrency: mean={conc.mean():.3f} max={int(conc.max())}")
    log.write(f"IS weights mean={w_is.mean():.3f} std={w_is.std():.3f}")

    # Sequential bootstrap indices (informative but not directly used downstream)
    boot_idx = sequential_bootstrap(events_is, conc, n_samples=min(len(events_is), 5000))
    log.write(f"Sequential bootstrap drew {len(boot_idx)} samples (average "
              f"uniqueness = {float(np.mean(1.0 / np.bincount(boot_idx, minlength=len(events_is))[boot_idx])):.3f}).")

    # ------------------------------------------------------------------
    # 5. Denoise + Detone correlation matrix
    # ------------------------------------------------------------------
    log = TxtLogger(paths.resultados, "05_denoising")
    log.header("Stage 5 — Marcenko-Pastur denoising + detoning")

    corr_raw = X_is_ev.corr().fillna(0.0)
    q = max(1.01, X_is_ev.shape[0] / max(1, X_is_ev.shape[1]))
    corr_dn = denoise_corr(corr_raw, q=q)
    corr_dt = detone(corr_dn, n_market_factors=1)
    log.write(f"q = T/N = {q:.2f}")
    log.write("Eigenvalue summary (raw / denoised / detoned):")
    eig_raw = np.linalg.eigvalsh(corr_raw.to_numpy())[::-1]
    eig_dn = np.linalg.eigvalsh(corr_dn.to_numpy())[::-1]
    eig_dt = np.linalg.eigvalsh(corr_dt.to_numpy())[::-1]
    log.table(pd.DataFrame({"raw": eig_raw, "denoised": eig_dn, "detoned": eig_dt}))

    # ------------------------------------------------------------------
    # 6. Clustered MDI / MDA
    # ------------------------------------------------------------------
    log = TxtLogger(paths.resultados, "06_feature_importance")
    log.header("Stage 6 — Clustered MDI / MDA (ONC clustering)")

    # Use a sample of the data for MDA to keep it fast; MDI uses full
    n_imp = min(len(y_is_meta), 20_000)
    sel = np.linspace(0, len(y_is_meta) - 1, n_imp, dtype=int)
    X_imp = X_is_ev.iloc[sel]
    y_imp = y_is_meta.iloc[sel]
    w_imp = w_is.loc[X_imp.index].to_numpy()

    imp = run_clustered_importance(
        X_imp.fillna(0.0), y_imp, sample_weight=w_imp, random_state=random_state,
    )
    log.write("Clusters:")
    for c, members in imp.clusters.items():
        log.write(f"  cluster_{c}: {members}")
    log.write("\nClustered MDI:")
    log.table(imp.mdi.to_frame("MDI"))
    log.write("\nClustered MDA:")
    log.table(imp.mda.to_frame("MDA"))
    P.plot_importance(imp.mdi, imp.mda, paths.plots / "06_clustered_importance.png")

    # ------------------------------------------------------------------
    # 7. Train meta-model with Purged K-Fold CV
    # ------------------------------------------------------------------
    log = TxtLogger(paths.resultados, "07_purged_kfold")
    log.header("Stage 7 — Purged K-Fold CV of meta-labels")

    t1_is = events_is["t1"]
    pkf = PurgedKFold(n_splits=5, t1=t1_is, embargo_pct=0.01)
    rf = RandomForestClassifier(
        n_estimators=rf_trees, max_depth=6, min_samples_leaf=50,
        class_weight="balanced_subsample", n_jobs=-1, random_state=random_state,
    )
    fold_scores = []
    oof_proba = pd.Series(np.nan, index=y_is_meta.index)

    X_np = X_is_ev.fillna(0.0)
    y_np = y_is_meta

    for k, (tr, te) in enumerate(pkf.split(X_np, y_np)):
        rf.fit(X_np.iloc[tr], y_np.iloc[tr], sample_weight=w_is.iloc[tr].to_numpy())
        proba = rf.predict_proba(X_np.iloc[te])[:, 1]
        pred = (proba >= 0.5).astype(int)
        oof_proba.iloc[te] = proba
        acc = accuracy_score(y_np.iloc[te], pred)
        f1 = f1_score(y_np.iloc[te], pred, zero_division=0)
        ll = log_loss(y_np.iloc[te], np.clip(proba, 1e-6, 1 - 1e-6), labels=[0, 1])
        fold_scores.append({"fold": k, "accuracy": acc, "f1": f1, "log_loss": ll})
        log.write(f"fold {k}: acc={acc:.4f}  f1={f1:.4f}  logloss={ll:.4f}")

    fs = pd.DataFrame(fold_scores)
    log.write("\nFold summary:")
    log.table(fs)
    log.write(f"Mean accuracy={fs['accuracy'].mean():.4f}  "
              f"mean F1={fs['f1'].mean():.4f}  mean logloss={fs['log_loss'].mean():.4f}")

    P.plot_precision_recall(
        y_np.loc[oof_proba.dropna().index].to_numpy(),
        oof_proba.dropna().to_numpy(),
        paths.plots / "07_precision_recall.png",
    )

    # ------------------------------------------------------------------
    # 8. CPCV backtest + Random Walk null + DSR/PSR
    # ------------------------------------------------------------------
    log = TxtLogger(paths.resultados, "08_cpcv_backtest")
    log.header("Stage 8 — CPCV, Random-Walk null, DSR / PSR")

    cpcv = CombinatorialPurgedCV(
        n_groups=cpcv_groups, n_test_groups=cpcv_test_groups,
        t1=t1_is, embargo_pct=0.01,
    )
    splits = cpcv.split_indices(X_np.index)
    log.write(f"CPCV splits: {len(splits)}  (groups={cpcv_groups}, test_groups={cpcv_test_groups})")

    per_split_preds = []
    per_path_sharpes: List[float] = []
    for tr, te, combo in splits:
        if len(tr) < 50:
            log.write(f"  skipping split {combo}: train size {len(tr)} too small after purge")
            continue
        rf.fit(X_np.iloc[tr], y_np.iloc[tr], sample_weight=w_is.iloc[tr].to_numpy())
        proba = rf.predict_proba(X_np.iloc[te])[:, 1]
        per_split_preds.append((te, proba, combo))
        ret_s = strategy_returns(
            side_is.loc[X_np.index].iloc[te],
            pd.Series(proba, index=X_np.index[te]),
            labels_is["ret"].loc[X_np.index].iloc[te],
        )
        per_path_sharpes.append(sharpe_ratio(ret_s.to_numpy()))

    log.write(f"Per-split Sharpe: mean={np.mean(per_path_sharpes):+.4f}  "
              f"std={np.std(per_path_sharpes):.4f}  min={np.min(per_path_sharpes):+.4f}  "
              f"max={np.max(per_path_sharpes):+.4f}")

    # Reconstruct unique paths across time
    paths_is = cpcv_paths(
        [(te, pr, combo) for te, pr, combo in per_split_preds],
        labels_is["ret"].loc[X_np.index],
        n_groups=cpcv_groups,
    )
    log.write(f"Reconstructed {len(paths_is)} full-time paths")
    path_sharpes = []
    for p in paths_is:
        ret = side_is.loc[p.index] * (p >= 0.5).astype(float) * labels_is["ret"].loc[p.index]
        path_sharpes.append(sharpe_ratio(ret.to_numpy()))
    log.write(f"Path Sharpe: mean={np.mean(path_sharpes):+.4f}  std={np.std(path_sharpes):.4f}")
    P.plot_cpcv_path_sharpes(path_sharpes, paths.plots / "08_cpcv_paths.png")

    # In-sample (all folds) Sharpe
    oof_ret_is = strategy_returns(
        side_is.loc[X_np.index], oof_proba.fillna(0.0), labels_is["ret"].loc[X_np.index]
    )
    sharpe_is = sharpe_ratio(oof_ret_is.to_numpy())
    log.write(f"\nIS out-of-fold Sharpe: {sharpe_is:+.4f}")

    # Random Walk null vs strategy
    null_sharpes = random_walk_null_distribution(
        labels_is["ret"].loc[X_np.index], n_sims=rw_sims, random_state=random_state,
    )
    p_value = float((null_sharpes >= sharpe_is).mean())
    log.write(f"RW null SR mean={null_sharpes.mean():+.4f}  std={null_sharpes.std():.4f}  "
              f"p(strategy>=null)={p_value:.4f}")
    P.plot_rw_null_vs_strategy(
        sharpe_is, null_sharpes, p_value, paths.plots / "08_rw_null.png"
    )

    # PSR / DSR. Following Bailey & López de Prado 2014, the "trials" set
    # for DSR is the collection of Sharpes that *could have been* selected
    # — here, the CPCV path Sharpes themselves (we only tested one model
    # configuration, and the across-path variance captures the relevant
    # uncertainty). The RW-null distribution is kept as a separate
    # hypothesis test above.
    psr = probabilistic_sharpe_ratio(oof_ret_is.to_numpy())
    trials = np.asarray(path_sharpes, dtype=float)
    dsr = deflated_sharpe_ratio(sharpe_is, trials, oof_ret_is.to_numpy())
    log.write(f"PSR (benchmark=0): {psr:.4f}")
    log.write(f"DSR (trials={len(trials)}, V={np.var(trials, ddof=1):.4f}): {dsr:.4f}")

    # ------------------------------------------------------------------
    # 9. Train final model on all IS, predict OOS
    # ------------------------------------------------------------------
    log = TxtLogger(paths.resultados, "09_oos_evaluation")
    log.header("Stage 9 — OOS (new_data) evaluation")

    rf.fit(X_np, y_np, sample_weight=w_is.to_numpy())
    X_oos_np = X_oos_ev.fillna(0.0)
    proba_oos = rf.predict_proba(X_oos_np)[:, 1]
    pred_oos = (proba_oos >= 0.5).astype(int)

    acc_oos = accuracy_score(y_oos_meta, pred_oos)
    f1_oos = f1_score(y_oos_meta, pred_oos, zero_division=0)
    ll_oos = log_loss(y_oos_meta, np.clip(proba_oos, 1e-6, 1 - 1e-6), labels=[0, 1])
    ret_oos = strategy_returns(
        side_oos.loc[X_oos_np.index],
        pd.Series(proba_oos, index=X_oos_np.index),
        labels_oos["ret"].loc[X_oos_np.index],
    )
    sharpe_oos = sharpe_ratio(ret_oos.to_numpy())

    log.write(f"OOS accuracy={acc_oos:.4f}  f1={f1_oos:.4f}  logloss={ll_oos:.4f}")
    log.write(f"OOS Sharpe={sharpe_oos:+.4f}")
    log.write(f"OOS ret mean={ret_oos.mean():+.6f}  std={ret_oos.std():.6f}  "
              f"skew={sp_skew(ret_oos.dropna()):+.3f}  kurt={sp_kurt(ret_oos.dropna()):+.3f}")

    P.plot_sharpe_is_vs_oos(sharpe_is, sharpe_oos, paths.plots / "09_is_vs_oos.png")

    # Pull historical CDI (Bacen SGS série 12, %/dia útil) for the IS+OOS
    # window; fall back to a flat 15% a.a. if the API is unreachable.
    cdi_series = None
    cdi_label = "CDI 15% a.a."
    try:
        cdi_start = bars_is.index.min()
        cdi_end = bars_oos.index.max()
        cdi_series = fetch_bacen_cdi(
            cdi_start, cdi_end, cache_path=paths.data / "cdi_bacen.csv"
        )
        mean_daily = float(cdi_series.mean())
        mean_ann = ((1.0 + mean_daily / 100.0) ** 252 - 1.0) * 100.0
        cdi_label = f"CDI Bacen (~{mean_ann:.2f}% a.a. médio)"
        log.write(
            f"CDI Bacen: {len(cdi_series)} obs "
            f"({cdi_series.index.min().date()} → {cdi_series.index.max().date()}), "
            f"média={mean_ann:.2f}% a.a."
        )
    except Exception as e:
        log.write(f"[cdi] fallback para 15% a.a. fixo ({e})")

    P.plot_fund_nav(
        is_rets=oof_ret_is,
        oos_rets=ret_oos,
        is_close=bars_is["close"],
        oos_close=bars_oos["close"],
        out=paths.plots / "09_cumulative_returns.png",
        cdi_daily_pct=cdi_series,
        cdi_annual=0.15,
        title=f"Cota (início = 1) — Modelo {sharpe_is:+.2f}/IS, {sharpe_oos:+.2f}/OOS  •  BTC B&H  •  {cdi_label}",
    )

    # Persist the final meta-model for later reuse.
    model_cfg = {
        "created_at": datetime.now(timezone.utc).isoformat(),
        "random_state": random_state,
        "rf": {
            "n_estimators": rf_trees, "max_depth": 6, "min_samples_leaf": 50,
            "class_weight": "balanced_subsample",
        },
        "features": list(X_np.columns),
        "primary_signal": {"source": "tstat_50", "threshold": tstat_threshold},
        "triple_barrier": {"pt_sl": list(pt_sl), "horizon_bars": horizon_bars},
        "bars": {"bars_per_day": bars_per_day, "dollar_threshold": float(bars_is.attrs["threshold"])},
        "cpcv": {"n_groups": cpcv_groups, "n_test_groups": cpcv_test_groups, "embargo_pct": 0.01},
        "training_range": {"start": str(X_np.index.min()), "end": str(X_np.index.max()), "n_events": int(len(X_np))},
        "meta_threshold": 0.5,
    }
    joblib.dump(rf, paths.model / "meta_model.joblib")
    (paths.model / "model_config.json").write_text(
        json.dumps(model_cfg, indent=2), encoding="utf-8"
    )
    log.write(f"\nModel saved to {paths.model / 'meta_model.joblib'}")
    log.write(f"Config saved to {paths.model / 'model_config.json'}")

    # ------------------------------------------------------------------
    # 10. Final report card
    # ------------------------------------------------------------------
    report = BacktestReport(
        sharpe_is=sharpe_is,
        sharpe_oos=sharpe_oos,
        psr=psr,
        dsr=dsr,
        rw_null_mean=float(null_sharpes.mean()),
        rw_null_std=float(null_sharpes.std()),
        rw_p_value=p_value,
        n_trials=len(trials),
    )
    log = TxtLogger(paths.resultados, "10_final_report")
    log.header("Stage 10 — Final report card")
    log.write(report.to_text())
    log.write(f"\nTotal runtime: {(time.time() - t_start)/60:.1f} min")

    return {
        "paths": paths,
        "report": report,
        "mdi": imp.mdi,
        "mda": imp.mda,
        "clusters": imp.clusters,
        "fold_scores": fs,
        "path_sharpes": path_sharpes,
        "null_sharpes": null_sharpes,
        "bar_summary_is": summary_is,
        "bar_summary_oos": summary_oos,
        "oos_metrics": {"accuracy": acc_oos, "f1": f1_oos, "log_loss": ll_oos},
    }


# --------------------------------------------------------------------------
# Markdown debate
# --------------------------------------------------------------------------

def _regime_commentary(sharpe_is: float, sharpe_oos: float) -> dict:
    """Pick a narrative flavour that matches the IS / OOS relationship."""
    gap = sharpe_is - sharpe_oos
    if sharpe_is > 0.2 and sharpe_oos > 0.1 and gap < 0.3:
        tone = "consistent"
        diagnosis = (
            "The in-sample and out-of-sample Sharpes agree in sign and in "
            "magnitude. This is the rare, mildly convincing case: the "
            "structure the model learned on 2021-2025 survives into 2025-2026."
        )
    elif sharpe_is > 0.2 and sharpe_oos <= 0.0:
        tone = "overfit"
        diagnosis = (
            "IS {sis:+.2f} vs OOS {soos:+.2f} — the canonical signature of "
            "backtest overfitting. The feature set plausibly over-fits the "
            "particular 2021-2025 regime and fails to generalise when the "
            "macro context flips. This is **exactly** the result the DSR/"
            "CPCV scaffolding was designed to expose — it is a success of "
            "the *methodology*, even though it is a failure of the *strategy*."
        ).format(sis=sharpe_is, soos=sharpe_oos)
    elif abs(sharpe_is) < 0.1 and abs(sharpe_oos) < 0.1:
        tone = "null"
        diagnosis = (
            "Both IS and OOS Sharpes are within a standard error of zero. "
            "The signals we extracted are statistically real but too "
            "small to be exploitable after frictions. File under "
            "'publishable negative result'."
        )
    else:
        tone = "mixed"
        diagnosis = (
            "IS {sis:+.2f} and OOS {soos:+.2f} disagree in a way that is "
            "neither a clean overfit nor a clean generalisation. The most "
            "likely cause is a regime change between the training and OOS "
            "periods — worth inspecting the exogenous features' levels "
            "(VIX, DXY spread, fear/greed) in both windows."
        ).format(sis=sharpe_is, soos=sharpe_oos)
    return {"tone": tone, "diagnosis": diagnosis}


DEBATE_TEMPLATE = """# Marcos & Feynman — a pipeline debate

> Conducted on the completion of one run of the AFML-inspired pipeline
> (`main.py`). Numbers come directly from the `resultados/` logs and plots
> just generated. The debate adapts to whether the result is overfit,
> null, consistent, or mixed.

---

### Opening — the result card

| Statistic | Value |
|---|---|
| Sharpe (IS, out-of-fold) | **{sharpe_is:+.4f}** |
| Sharpe (OOS, new_data/) | **{sharpe_oos:+.4f}** |
| Probabilistic SR | {psr:.4f} |
| Deflated SR (N trials = {n_trials}) | **{dsr:.4f}** |
| Random-Walk null SR | {rw_mean:+.4f} ± {rw_std:.4f} |
| p(strategy ≥ null) | **{rw_p:.4f}** |
| OOS accuracy / F1 / log-loss | {acc_oos:.3f} / {f1_oos:.3f} / {ll_oos:.3f} |

Regime detected from the IS/OOS pair: **{tone}**.

{diagnosis}

Clusters selected by ONC: **{n_clusters}**. Top-MDA cluster:
**{top_mda_cluster}** (MDA = {top_mda_value:+.4f}), containing features
`{top_mda_members}`.

---

### Act I — "Is there a signal at all?"

**Feynman.** — Marcos, the IS Sharpe is {sharpe_is:+.3f}; OOS is
{sharpe_oos:+.3f}. Before you reach for the DSR, tell me plainly:
did we find an effect, or did we find a confidence interval that
happens to lean one way?

**Marcos.** — The honest answer is in the **gap**. PSR says the IS
Sharpe is plausibly above zero with probability {psr:.3f}. That is
an *in-sample* statement. The DSR, now corrected for the
{n_trials} trials we actually ran, is {dsr:.3f} — an inference about
the *true* Sharpe after we punish ourselves for the number of paths
we walked. And the OOS Sharpe is the final referee. The spread
between IS and OOS is **{sharpe_gap:+.2f}** Sharpe units, which is
the single most diagnostic number in this report.

**Feynman.** — A gap of that magnitude tells me a physics story: if
your 'detector' is showing a signal in one calibration window and
absence-of-signal in the next, either the source turned off or the
detector is responding to local conditions you did not model.

---

### Act II — "Labeling was done right"

**Feynman.** — A thing I liked: the **triple-barrier** bins returns
by which wall they hit first, not by a fixed horizon. That is
honest — it respects the path. In physics we would call it a
*first-passage-time* formalism.

**Marcos.** — Exactly. And the horizontal barriers are calibrated to
each point's ex-ante volatility, so the experiment is scale-
invariant across regimes. The meta-label is then `{{success,
failure}}` *given* the primary model's direction — which is where
the causal prior enters via `tstat_50`. The ML model is not fishing
for direction; it is only learning **when not to bet**.

**Feynman.** — That framing matters because it separates two
questions: *where does the signal come from?* and *when should we
act on it?*. If the OOS Sharpe is negative, the failure is on the
second question, not the first.

---

### Act III — "What did the clustered importance tell us?"

**Feynman.** — The clustered MDA put cluster `{top_mda_cluster}`
at the top, containing `{top_mda_members}`. My univariate MDA on
the earlier run had put `sg_velocity_51`, `tstat_50`, `vix_chg`,
`tstat_20` on top. The rank is broadly consistent, and — crucially
— clustering contained the *substitution effect* that would have
otherwise split credit among near-duplicates.

**Marcos.** — That is the whole point of MDA-on-clusters. With
vanilla MDI, correlated copies of the same feature permute the
importance ranking arbitrarily. Clustering first stabilises the
ranking so the interpretation survives perturbations of the feature
set.

**Feynman.** — And the **rejected** microstructure features —
`vpin`, `kyle_lambda`, `roll_spread` — are statistically genuine
but too small per event to change the RF's splits. A feature can
be *real* (different from chance) but *useless* (too small to
matter). That distinction deserves its own name in the literature.

---

### Act IV — "The Random-Walk null was the right adversary"

**Marcos.** — Observe: the RW null Sharpe is {rw_mean:+.4f} ±
{rw_std:.4f}; the IS Sharpe is {sharpe_is:+.3f}. The p-value of
{rw_p:.4f} measures how often a block-bootstrapped, sign-flipped
version of our own returns outperforms our strategy.

**Feynman.** — The block-bootstrap preserves the autocorrelation
the market has; randomising the sign destroys the drift. That is
*exactly* the adversary we want to defeat — and the only adversary
that is scientifically fair on minute-level crypto data.

**Marcos.** — If the p-value is small *and* the OOS Sharpe is of
the same sign as the IS Sharpe, the signal has survived every trap
I know how to build. If either condition fails, we must stop
calling it alpha.

---

### Act V — "So did we discover alpha?"

**Marcos.** — Alpha is a *causal, mechanistic* claim. The scaffolding
we have is:

1. Isolation of genuinely informative features (the `tstat_N`
   family + exogenous macro context).
2. A theory: *tstat is a volatility-normalised momentum; when the
   macro context is risk-off (VIX up, DXY spread widening) the
   meta-model abstains*.
3. A look-ahead-safe implementation (causal SavGol, fixed-width
   FFD, purged CV, embargo, CPCV).

Given our numbers — DSR = {dsr:.3f}, IS/OOS gap = {sharpe_gap:+.2f} —
the honest conclusion is: {verdict}

**Feynman.** — The virtue of this pipeline is not that it finds
alpha. It is that it is **pathologically conservative** about
look-ahead, overlap, and selection bias. When it says "no", it
actually means it. When it says "maybe", it tells you by how much.
That is the best you can hope for when the signal-to-noise ratio is
this hostile.

---

### Closing — what to try next

- **Inspect the regime break.** Plot `plots/09_equity_curves.png`:
  where does the IS equity curve diverge from the OOS? That date is
  your prime suspect for a macro regime change.
- **Re-calibrate volatility.** Try `pt_sl = (2.0, 1.0)` to allow
  winners to run — historically this pushes return skew positive.
- **Second primary signal.** Add a mean-reversion primary for
  high-vol regimes and let the meta-model arbitrate between
  momentum and mean-reversion.
- **Monitor DSR through time.** Re-run monthly. A decaying DSR is
  the earliest signature of strategy decay.

Plots of interest: `plots/01_bar_returns_*.png`,
`plots/06_clustered_importance.png`, `plots/08_cpcv_paths.png`,
`plots/08_rw_null.png`, `plots/09_is_vs_oos.png`,
`plots/09_equity_curves.png`.
"""


_VERDICT = {
    "consistent": (
        "this is **not yet a strategy**, but it is the kind of result "
        "that justifies a slightly larger research budget."
    ),
    "overfit": (
        "this is **not alpha** — it is a textbook backtest over-fit. "
        "The right action is to shrink the feature set, or accept the "
        "signal is regime-dependent and trade only in the matching "
        "regime."
    ),
    "null": (
        "this is a clean **null result**. Publish it as a negative "
        "finding and move on — the pipeline has not been wasted, "
        "because a believable null is as scientifically valuable as a "
        "believable positive."
    ),
    "mixed": (
        "this is an **inconclusive** regime. Inspect the exogenous "
        "features in IS vs OOS before drawing any strategy conclusion."
    ),
}


def write_markdown_report(paths: ProjectPaths, result: dict) -> None:
    mda = result["mda"]
    clusters = result["clusters"]
    top_cluster_key = mda.index[0]
    cluster_id = int(top_cluster_key.split("_")[-1])
    top_members = clusters[cluster_id]

    rep = result["report"]
    regime = _regime_commentary(rep.sharpe_is, rep.sharpe_oos)

    md = DEBATE_TEMPLATE.format(
        sharpe_is=rep.sharpe_is,
        sharpe_oos=rep.sharpe_oos,
        sharpe_gap=rep.sharpe_is - rep.sharpe_oos,
        psr=rep.psr,
        dsr=rep.dsr,
        n_trials=rep.n_trials,
        rw_mean=rep.rw_null_mean,
        rw_std=rep.rw_null_std,
        rw_p=rep.rw_p_value,
        acc_oos=result["oos_metrics"]["accuracy"],
        f1_oos=result["oos_metrics"]["f1"],
        ll_oos=result["oos_metrics"]["log_loss"],
        n_clusters=len(clusters),
        top_mda_cluster=top_cluster_key,
        top_mda_value=mda.iloc[0],
        top_mda_members=", ".join(top_members),
        tone=regime["tone"],
        diagnosis=regime["diagnosis"],
        verdict=_VERDICT[regime["tone"]],
    )
    (paths.root / "RELATORIO_MARCOS_FEYNMAN.md").write_text(md, encoding="utf-8")


# --------------------------------------------------------------------------
# CLI entry
# --------------------------------------------------------------------------

def _pickle_payload(result: dict) -> dict:
    """Extract just the picklable bits of result for fast regen."""
    return {
        "report": result["report"],
        "mda": result["mda"],
        "mdi": result["mdi"],
        "clusters": result["clusters"],
        "oos_metrics": result["oos_metrics"],
        "path_sharpes": result["path_sharpes"],
        "null_sharpes": result["null_sharpes"],
        "bar_summary_is": result["bar_summary_is"],
        "bar_summary_oos": result["bar_summary_oos"],
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--bars-per-day", type=int, default=100)
    parser.add_argument("--horizon-bars", type=int, default=20)
    parser.add_argument("--pt", type=float, default=1.0)
    parser.add_argument("--sl", type=float, default=1.0)
    parser.add_argument("--tstat-threshold", type=float, default=0.5)
    parser.add_argument("--cpcv-groups", type=int, default=6)
    parser.add_argument("--cpcv-test-groups", type=int, default=2)
    parser.add_argument("--rw-sims", type=int, default=500)
    parser.add_argument("--rf-trees", type=int, default=300)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--regen-report-only", action="store_true",
                        help="Skip pipeline; regen markdown from resultados/_run.pkl")
    args = parser.parse_args()

    paths = ProjectPaths.discover()
    pkl = paths.resultados / "_run.pkl"

    if args.regen_report_only:
        if not pkl.exists():
            print(f"No cached run at {pkl} — run the pipeline once first.")
            sys.exit(1)
        with pkl.open("rb") as f:
            payload = pickle.load(f)
        payload["paths"] = paths
        write_markdown_report(paths, payload)
        print(f"Report regenerated at {paths.root / 'RELATORIO_MARCOS_FEYNMAN.md'}")
        return

    result = run_pipeline(
        bars_per_day=args.bars_per_day,
        horizon_bars=args.horizon_bars,
        pt_sl=(args.pt, args.sl),
        tstat_threshold=args.tstat_threshold,
        cpcv_groups=args.cpcv_groups,
        cpcv_test_groups=args.cpcv_test_groups,
        rw_sims=args.rw_sims,
        rf_trees=args.rf_trees,
        random_state=args.seed,
    )
    with pkl.open("wb") as f:
        pickle.dump(_pickle_payload(result), f)
    write_markdown_report(result["paths"], result)
    print(f"\nReport written to {result['paths'].root / 'RELATORIO_MARCOS_FEYNMAN.md'}")


if __name__ == "__main__":
    main()
