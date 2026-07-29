# -*- coding: utf-8 -*-
"""
04_train_final.py — Treina e persiste os artefatos finais sobre todo o histórico.

Dois artefatos (consenso: "a regressão é a pesquisa; o classificador é o produto"):
  - model_ridge.pkl   : ridge do resíduo (bps), features default (SEM USDT — ablação reprovou)
  - model_regime.pkl  : logística P(|resíduo| > custo) -> "dolar_cc é confiável hoje?"

O veredito do walk-forward (03) manda: se NO-GO, o ridge é usado apenas como sinal
direcional em paper trading; o produto principal é dolar_cc + classificador de regime.
"""
import os, json
import numpy as np
import pandas as pd
import joblib
from sklearn.linear_model import Ridge, LogisticRegression
from sklearn.preprocessing import StandardScaler

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
PROC = os.path.join(ROOT, "data", "processed")
RES = os.path.join(ROOT, "results")
MODELS = os.path.join(ROOT, "models")
THRESH_BPS = 8.0
FEATS = ["ret_fut_on", "ret_dxy_on", "vol_6l_on", "event_day", "basis_lag1"]
REGIME_FEATS = ["vol_6l_on", "event_day", "abs_ret_fut_on", "abs_basis_lag1"]

df = pd.read_csv(os.path.join(PROC, "dataset_daily.csv"), parse_dates=["date"]).set_index("date")
df["abs_ret_fut_on"] = df["ret_fut_on"].abs()
df["abs_basis_lag1"] = df["basis_lag1"].abs()
df = df.dropna(subset=FEATS + ["y_log_resid"])
y = df["y_log_resid"].values * 1e4

# --- ridge final (alpha=10, vencedor consistente do walk-forward interno)
sc = StandardScaler().fit(df[FEATS].values)
ridge = Ridge(alpha=10.0).fit(sc.transform(df[FEATS].values), y)

# --- IC dos coeficientes por bootstrap em blocos (blocos de 10 dias)
rng = np.random.default_rng(42)
B, block, coefs = 1000, 10, []
Xs = sc.transform(df[FEATS].values)
for _ in range(B):
    starts = rng.integers(0, len(y) - block, size=len(y) // block + 1)
    idx = np.concatenate([np.arange(s, s + block) for s in starts])[: len(y)]
    coefs.append(Ridge(alpha=10.0).fit(Xs[idx], y[idx]).coef_)
coefs = np.array(coefs)
lo, hi = np.percentile(coefs, [2.5, 97.5], axis=0)
print("Coeficientes do ridge (bps por sd da feature), IC 95% bootstrap em blocos:")
for f, c, a, b in zip(FEATS, ridge.coef_, lo, hi):
    star = " *" if np.sign(a) == np.sign(b) else ""
    print(f"  {f:<14} {c:+6.2f}  [{a:+6.2f}, {b:+6.2f}]{star}")
print(f"  intercepto     {ridge.intercept_:+6.2f}  (média incondicional da basis)")

# --- classificador de regime
yr = (np.abs(y) > THRESH_BPS).astype(int)
sc_r = StandardScaler().fit(df[REGIME_FEATS].values)
regime = LogisticRegression(C=1.0).fit(sc_r.transform(df[REGIME_FEATS].values), yr)
acc = regime.score(sc_r.transform(df[REGIME_FEATS].values), yr)
print(f"\nRegime: P(|basis| > {THRESH_BPS:.0f} bps) — base rate={yr.mean():.2f}, acc in-sample={acc:.2f}")

meta = {"feats": FEATS, "regime_feats": REGIME_FEATS, "thresh_bps": THRESH_BPS,
        "alpha": 10.0, "trained_through": str(df.index[-1].date()),
        "n_train": int(len(y)), "basis_mean_bps": float(y.mean()),
        "veredito_walkforward": json.load(open(os.path.join(RES, "configs_registry.json"),
                                               encoding="utf-8"))["veredito"]}
joblib.dump({"scaler": sc, "model": ridge, **meta}, os.path.join(MODELS, "model_ridge.pkl"))
joblib.dump({"scaler": sc_r, "model": regime, **meta}, os.path.join(MODELS, "model_regime.pkl"))
with open(os.path.join(MODELS, "model_meta.json"), "w", encoding="utf-8") as f:
    json.dump(meta, f, ensure_ascii=False, indent=2)
print(f"\nSalvos: model_ridge.pkl, model_regime.pkl, model_meta.json (treinado até {meta['trained_through']})")
