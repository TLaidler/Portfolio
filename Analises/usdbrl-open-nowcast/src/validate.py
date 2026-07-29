# -*- coding: utf-8 -*-
"""
03_validate.py — Walk-forward expandindo + benchmarks + Diebold-Mariano + ablação USDT.

Esquema (consenso do debate):
  - treino inicial 60 dias úteis, passo 5, embargo 2 dias entre fim do treino e teste
  - benchmarks: b1 = basis zero (open = dolar_cc); b2 = média móvel 20d da basis (causal)
  - modelo: ridge com features padronizadas (scaler fitado SÓ no treino de cada fold)
  - ablação USDT/BRL (ressalva do usuário): mesma validação com e sem o bloco USDT
  - go/no-go: MAE >=15% melhor que b2, DM p<0.10, direcional >58% nos dias acionáveis,
    estabilidade nas duas metades

Registro de configurações (PBO/DSR - freio contra seleção): configs_registry.json
"""
import os, json
import numpy as np
import pandas as pd
from scipy import stats
from sklearn.linear_model import Ridge
from sklearn.preprocessing import StandardScaler

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
PROC = os.path.join(ROOT, "data", "processed")
RES = os.path.join(ROOT, "results")
INIT_TRAIN, STEP, EMBARGO = 60, 5, 2
THRESH_BPS = 8.0            # dia acionável: |previsão| > custo típico
ALPHAS = [1.0, 10.0, 100.0]

FEATS_DEFAULT = ["ret_fut_on", "ret_dxy_on", "vol_6l_on", "event_day", "basis_lag1"]
FEATS_USDT = FEATS_DEFAULT + ["ret_usdt_on", "usdt_premium_snap"]

df = pd.read_csv(os.path.join(PROC, "dataset_daily.csv"), parse_dates=["date"]).set_index("date")
df = df.dropna(subset=FEATS_USDT + ["y_log_resid"])
y = (df["y_log_resid"] * 1e4).values          # bps
n = len(df)
print(f"N = {n} dias após dropna | walk-forward: treino inicial {INIT_TRAIN}, passo {STEP}, embargo {EMBARGO}")

def ridge_inner_alpha(Xtr, ytr):
    """Escolhe alpha por mini walk-forward DENTRO do treino (sem shuffle, sem vazamento)."""
    if len(ytr) < 40:
        return ALPHAS[1]
    cut = int(len(ytr) * 0.75)
    best, best_mae = ALPHAS[1], np.inf
    sc = StandardScaler().fit(Xtr[:cut])
    for a in ALPHAS:
        m = Ridge(alpha=a).fit(sc.transform(Xtr[:cut]), ytr[:cut])
        mae = np.abs(ytr[cut:] - m.predict(sc.transform(Xtr[cut:]))).mean()
        if mae < best_mae:
            best, best_mae = a, mae
    return best

def walk_forward(feats):
    X = df[feats].values.astype(float)
    preds, idxs = [], []
    for start in range(INIT_TRAIN, n, STEP):
        tr_end = start - EMBARGO
        test = range(start, min(start + STEP, n))
        Xtr, ytr = X[:tr_end], y[:tr_end]
        a = ridge_inner_alpha(Xtr, ytr)
        sc = StandardScaler().fit(Xtr)
        m = Ridge(alpha=a).fit(sc.transform(Xtr), ytr)
        for t in test:
            preds.append(m.predict(sc.transform(X[t:t + 1]))[0])
            idxs.append(t)
    return np.array(preds), np.array(idxs)

def b2_pred(idxs):
    """Média móvel 20d da basis usando apenas y até D-1 (causal: y_{t-1} é conhecido às 8:50)."""
    s = pd.Series(y)
    roll = s.shift(1).rolling(20, min_periods=10).mean()
    return roll.values[idxs]

def dm_test(e1, e2):
    """Diebold-Mariano (h=1, perda absoluta) com correção de amostra pequena HLN."""
    d = np.abs(e1) - np.abs(e2)
    nn = len(d)
    dm = d.mean() / np.sqrt(d.var(ddof=1) / nn)
    hln = dm * np.sqrt((nn + 1 - 2 + 0) / nn)     # h=1
    p = 2 * (1 - stats.t.cdf(abs(hln), df=nn - 1))
    return hln, p

def evaluate(name, pred, idxs):
    truth = y[idxs]
    e = truth - pred
    mae, rmse = np.abs(e).mean(), np.sqrt((e ** 2).mean())
    act = np.abs(pred) > THRESH_BPS
    dir_acc = (np.sign(pred[act]) == np.sign(truth[act])).mean() if act.sum() > 0 else np.nan
    half = len(e) // 2
    return {"config": name, "n_oos": len(e), "MAE": mae, "RMSE": rmse,
            "MAE_1a_metade": np.abs(e[:half]).mean(), "MAE_2a_metade": np.abs(e[half:]).mean(),
            "dias_acionaveis": int(act.sum()), "direcional_acionavel": dir_acc}

# ---------------- roda tudo ----------------
pred_ridge, idxs = walk_forward(FEATS_DEFAULT)
pred_usdt, _ = walk_forward(FEATS_USDT)
pred_b1 = np.zeros(len(idxs))
pred_b2 = b2_pred(idxs)

results = [evaluate("b1_basis_zero", pred_b1, idxs),
           evaluate("b2_media_movel_20d", pred_b2, idxs),
           evaluate("ridge_default", pred_ridge, idxs),
           evaluate("ridge_com_usdt", pred_usdt, idxs)]
res = pd.DataFrame(results).set_index("config")
print("\n" + res.round(2).to_string())

# ---------------- DM tests ----------------
truth = y[idxs]
print("\n--- Diebold-Mariano (perda absoluta, HLN small-sample) ---")
pairs = [("ridge_default", truth - pred_ridge, "b1", truth - pred_b1),
         ("ridge_default", truth - pred_ridge, "b2", truth - pred_b2),
         ("ridge_com_usdt", truth - pred_usdt, "b2", truth - pred_b2),
         ("ridge_com_usdt", truth - pred_usdt, "ridge_default", truth - pred_ridge)]
dm_out = {}
for n1, e1, n2, e2 in pairs:
    s, p = dm_test(e1, e2)
    dm_out[f"{n1}_vs_{n2}"] = {"dm": round(float(s), 3), "p": round(float(p), 4)}
    verdict = "melhor" if s < 0 else "pior"
    sig = "significativo" if p < 0.10 else "sem significância"
    print(f"{n1} vs {n2}: DM={s:+.2f}, p={p:.4f} ({verdict} que {n2}, {sig})")

# ---------------- ablação USDT (ressalva do usuário) ----------------
print("\n--- Ablação USDT/BRL ---")
mae_d, mae_u = res.loc["ridge_default", "MAE"], res.loc["ridge_com_usdt", "MAE"]
delta = (mae_u - mae_d) / mae_d * 100
print(f"MAE default={mae_d:.2f} vs com USDT={mae_u:.2f} bps ({delta:+.1f}%)")
h = len(idxs) // 2
e_d, e_u = np.abs(truth - pred_ridge), np.abs(truth - pred_usdt)
print(f"metades (default -> usdt): 1ª {e_d[:h].mean():.2f}->{e_u[:h].mean():.2f}, "
      f"2ª {e_d[h:].mean():.2f}->{e_u[h:].mean():.2f}")
usdt_verdict = "REPROVADO" if mae_u >= mae_d * 0.99 else "verificar estabilidade"
print(f"Veredito ablação: USDT {usdt_verdict} (modelo default permanece SEM USDT)")

# ---------------- go/no-go ----------------
print("\n--- GO/NO-GO (consenso item 9) ---")
mae_b2 = res.loc["b2_media_movel_20d", "MAE"]
improve = (mae_b2 - mae_d) / mae_b2 * 100
p_b2 = dm_out["ridge_default_vs_b2"]["p"]
dir_ok = res.loc["ridge_default", "direcional_acionavel"]
halves = res.loc["ridge_default", ["MAE_1a_metade", "MAE_2a_metade"]].values
b2_halves = res.loc["b2_media_movel_20d", ["MAE_1a_metade", "MAE_2a_metade"]].values
stable = bool((halves < b2_halves).all())
checks = {
    "MAE >=15% melhor que b2": improve >= 15,
    "DM p<0.10 vs b2": p_b2 < 0.10,
    "direcional >58% (acionáveis)": bool(dir_ok > 0.58) if not np.isnan(dir_ok) else False,
    "estável nas 2 metades": stable,
}
for k, v in checks.items():
    print(f"  [{'x' if v else ' '}] {k}")
go = all(checks.values())
print(f"\nVEREDITO: {'GO - modelo aprovado' if go else 'NO-GO - entregar dolar_cc + classificador de regime (resposta honesta do consenso)'}")
print(f"(melhora sobre b2: {improve:+.1f}% | p={p_b2} | direcional={dir_ok if not np.isnan(dir_ok) else float('nan'):.2f} | estável={stable})")

# ---------------- registry ----------------
registry = {
    "nota": "Registro de todas as configurações avaliadas (freio PBO/DSR do consenso: "
            "qualquer variante testada e descartada deve constar aqui).",
    "atuais": {r["config"]: {k: (None if isinstance(v, float) and np.isnan(v) else
                                 (round(float(v), 3) if isinstance(v, (int, float, np.floating)) else v))
                             for k, v in r.items() if k != "config"} for r in results},
    "dm_tests": dm_out,
    "params": {"init_train": INIT_TRAIN, "step": STEP, "embargo": EMBARGO,
               "thresh_bps": THRESH_BPS, "alphas": ALPHAS, "feats_default": FEATS_DEFAULT,
               "feats_usdt": FEATS_USDT},
    "go_no_go": {k: bool(v) for k, v in checks.items()}, "veredito": "GO" if go else "NO-GO",
}
with open(os.path.join(RES, "configs_registry.json"), "w", encoding="utf-8") as f:
    json.dump(registry, f, ensure_ascii=False, indent=2)

oos = pd.DataFrame({"date": df.index[idxs], "y_true_bps": truth, "pred_ridge": pred_ridge,
                    "pred_ridge_usdt": pred_usdt, "pred_b2": pred_b2}).set_index("date")
oos.to_csv(os.path.join(RES, "walkforward_oos.csv"))
print("\nSalvos: configs_registry.json, walkforward_oos.csv")
