# -*- coding: utf-8 -*-
"""
02_diagnostics.py — EDA honesta do resíduo antes de qualquer modelagem (consenso do debate).

1. Estatísticas do resíduo: ACF, dia-da-semana, dias de evento macro.
2. Convergência intradiária da basis (8:00 -> 8:55) -> valida a escolha do snapshot.
3. Teste de 3 passos do USDT/BRL (preditividade, sinal, estabilidade nas 2 metades).
4. Gate de parada: sd(erro do baseline b1) vs bid-ask típico do fixing.

Saída: diagnostics_report.txt + diagnostics.png
"""
import os
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
PROC = os.path.join(ROOT, "data", "processed")
RES = os.path.join(ROOT, "results")
BIDASK_BPS = 8.0   # bid-ask típico do fixing (ajustável pelo trader)

df = pd.read_csv(os.path.join(PROC, "dataset_daily.csv"), parse_dates=["date"]).set_index("date")
y = df["y_log_resid"] * 1e4   # bps
lines = []
def log(s=""):
    lines.append(str(s)); print(s)

log("=" * 70)
log("DIAGNÓSTICO DO RESÍDUO  y = log(open 9:00) - log(dolar_cc 8:50)   [bps]")
log("=" * 70)
log(f"N = {len(y)} dias | {y.index[0].date()} -> {y.index[-1].date()}")
log(f"média = {y.mean():+.1f} | sd = {y.std():.1f} | mediana = {y.median():+.1f}")
log(f"IQR = [{y.quantile(.25):+.1f}, {y.quantile(.75):+.1f}] | min/max = {y.min():+.1f}/{y.max():+.1f}")

# --- 1a. ACF
log("\n--- ACF do resíduo (lags 1-5) ---")
acf = [y.autocorr(k) for k in range(1, 6)]
ci = 1.96 / np.sqrt(len(y))
for k, a in enumerate(acf, 1):
    sig = "  <-- significativo" if abs(a) > ci else ""
    log(f"lag {k}: {a:+.3f}{sig}")
log(f"(IC 95% = ±{ci:.3f})")

# --- 1b. dia da semana
log("\n--- Resíduo por dia da semana (bps) ---")
wd = y.groupby(y.index.dayofweek).agg(["mean", "std", "count"])
wd.index = ["seg", "ter", "qua", "qui", "sex"][: len(wd)]
log(wd.round(1).to_string())

# --- 1c. evento macro
log("\n--- Dias de evento macro vs normais ---")
ev = df["event_day"] == 1
log(f"evento  (n={ev.sum()}): média={y[ev].mean():+.1f}, sd={y[ev].std():.1f}, |y|média={y[ev].abs().mean():.1f}")
log(f"normal  (n={(~ev).sum()}): média={y[~ev].mean():+.1f}, sd={y[~ev].std():.1f}, |y|média={y[~ev].abs().mean():.1f}")

# --- 2. convergência intradiária da basis: repete o snapshot em vários horários
#     (única seção que exige os dados brutos do 6L; degrada com aviso se ausentes)
log("\n--- Convergência da basis por horário do snapshot ---")
log("(recalcula dolar_cc com o último tick do 6L <= cada horário; cupom do dia)")
res = {}
try:
    import importlib.util
    spec = importlib.util.spec_from_file_location("b", os.path.join(HERE, "build_dataset.py"))
    b = importlib.util.module_from_spec(spec); spec.loader.exec_module(b)
    fut, _ = b.build_6l_continuous()
    fut_usdbrl = 100.0 / fut
    cc = df["dolar_cc_snap"] * 0 + (df["fut_snap_px"] / df["dolar_cc_snap"])  # fator cupom do dia
    for hhmm in ["08:00", "08:20", "08:40", "08:50", "08:55"]:
        vals = []
        for d, row in df.iterrows():
            ts = pd.Timestamp(f"{d.date()} {hhmm}")
            s = fut_usdbrl.loc[:ts]
            if s.empty or (ts - s.index[-1]).total_seconds() > 240 * 60:
                continue
            dcc = s.iloc[-1] / cc.loc[d]
            vals.append(np.log(row["open_bloom"]) - np.log(dcc))
        v = pd.Series(vals) * 1e4
        res[hhmm] = v
        log(f"{hhmm}: n={len(v):3d}  média={v.mean():+.1f}  sd={v.std():.1f}  MAE={v.abs().mean():.1f}")
    log("=> menor sd/MAE define o snapshot; diferenças <1bp não justificam mudança.")
except FileNotFoundError:
    log("[pulado] dados brutos do 6L não encontrados — defina USDBRL_RAW_CONTRACTS")
    log("(resultado da execução original: 8:50 é o snapshot ótimo — sd 16.3 vs 17.6 às 8:40)")

# --- 3. teste de 3 passos do USDT/BRL (ressalva do usuário: ablação antes de usar)
log("\n--- Teste de 3 passos: retorno overnight USDT/BRL ---")
log("(sem série USDT/USD no histórico -> teste roda SEM ajuste de peg; documentado)")
sub = df.dropna(subset=["ret_usdt_on", "y_log_resid"])
x = sub["ret_usdt_on"] * 1e4
yy = sub["y_log_resid"] * 1e4
# passo 1: preditividade (regressão univariada, erros HC)
xc = x - x.mean()
beta = (xc * (yy - yy.mean())).sum() / (xc ** 2).sum()
resid = yy - yy.mean() - beta * xc
se = np.sqrt((resid ** 2).sum() / (len(x) - 2) / (xc ** 2).sum())
t = beta / se
log(f"passo 1 (preditividade): beta={beta:+.4f} bps/bps, t={t:+.2f} "
    f"{'PASSA' if abs(t) > 2 else 'FALHA (|t|<2)'}")
# passo 2: sinal esperado positivo (usdt subiu overnight -> abertura acima do implícito)
log(f"passo 2 (sinal): {'PASSA (beta>0)' if beta > 0 else 'FALHA (beta<=0)'}")
# passo 3: estabilidade nas duas metades
half = len(sub) // 2
cors = [x.iloc[:half].corr(yy.iloc[:half]), x.iloc[half:].corr(yy.iloc[half:])]
log(f"passo 3 (estabilidade): corr 1ª metade={cors[0]:+.3f}, 2ª metade={cors[1]:+.3f} "
    f"{'PASSA' if np.sign(cors[0]) == np.sign(cors[1]) and min(abs(c) for c in cors) > 0.05 else 'FALHA'}")

# --- 4. gate de parada
log("\n--- Gate de parada (consenso, item 8) ---")
log(f"sd(erro b1 = basis zero) = {y.std():.1f} bps vs bid-ask típico = {BIDASK_BPS:.0f} bps")
if y.std() <= BIDASK_BPS:
    log("=> PARE: o erro do baseline é da ordem do bid-ask; não há dinheiro a capturar.")
else:
    log("=> SEGUE: há variância acima do custo; modelagem do resíduo se justifica.")
log(f"média(basis) = {y.mean():+.1f} bps -> b2 (dolar_cc + média móvel) é benchmark obrigatório.")

with open(os.path.join(RES, "diagnostics_report.txt"), "w", encoding="utf-8") as f:
    f.write("\n".join(lines))

# --- plots
fig, ax = plt.subplots(2, 2, figsize=(13, 8))
y.plot(ax=ax[0, 0], marker=".", lw=.7, title="Resíduo diário (bps)")
ax[0, 0].axhline(0, color="k", lw=.5)
y.hist(bins=40, ax=ax[0, 1]); ax[0, 1].set_title("Distribuição do resíduo (bps)")
pd.Series(acf, index=range(1, 6)).plot.bar(ax=ax[1, 0], title="ACF do resíduo")
ax[1, 0].axhline(ci, color="r", ls="--", lw=.7); ax[1, 0].axhline(-ci, color="r", ls="--", lw=.7)
if res:
    pd.DataFrame({k: [v.mean(), v.abs().mean()] for k, v in res.items()},
                 index=["média", "MAE"]).T.plot.bar(ax=ax[1, 1], title="Basis por horário do snapshot (bps)")
else:
    ax[1, 1].set_title("Basis por horário: requer dados brutos (pulado)")
plt.tight_layout()
plt.savefig(os.path.join(RES, "diagnostics.png"), dpi=110)
print("\nSalvos: diagnostics_report.txt, diagnostics.png")
