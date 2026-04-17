#!/usr/bin/env python3
# coding: utf-8
"""
T8 para Mod3: Random Walk Null Model — ret_50 (raw vs SavGol vs MA)

Pergunta: O SR de sign(ret_50) em dollar bars (20/dia) é genuíno ou artefato?
Testa 3 variantes do filtro, cada uma contra 200 random walks drift=0.

Resultado esperado:
  - Se p < 0.05 → feature GENUÍNA (SR não explicável por random walk)
  - Se p >= 0.05 → ARTEFATO (autocorrelação do filtro explica o SR)
"""

import os
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from scipy import stats as sp_stats
from utils.savgol import savgol_causal
from regime_detection_advanced import DollarBarBuilder, DEFAULT_CONFIG

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(SCRIPT_DIR, "data")
SAVE_DIR = os.path.join(SCRIPT_DIR, "relatorios", "pngs")
os.makedirs(SAVE_DIR, exist_ok=True)

SG_WINDOW = 51  # Mod3 usa ret_50, SavGol janela 51 para compatibilidade
SG_POLY = 3
RET_WINDOW = 50  # ret_50 — horizonte do Mod3
N_SIMS = 200


def load_dollar_bars() -> pd.DataFrame:
    """Carrega BTC 1-min e gera dollar bars (20/dia)."""
    path = os.path.join(DATA_DIR, "btcusdt_1m.csv")
    df = pd.read_csv(path, parse_dates=["timestamp"])
    print(f"  BTC 1-min: {df.shape}")

    builder = DollarBarBuilder(
        calibration_days=DEFAULT_CONFIG["dollar_bar_calibration_days"],
        bars_per_day=20,  # Mod3 config
    )
    builder.calibrate_threshold(df)
    bars = builder.transform(df)
    print(f"  Dollar bars: {len(bars)} (~{len(bars) / ((bars['timestamp'].iloc[-1] - bars['timestamp'].iloc[0]).total_seconds() / 86400):.0f}/dia)")
    return bars


def compute_sr(close: np.ndarray, ret_window: int, filter_fn) -> float:
    """Aplica filtro, calcula sign(ret_N), retorna SR per-bar."""
    close_filtered = filter_fn(close)
    signal = pd.Series(close_filtered).pct_change(ret_window).values
    actual_ret = np.diff(close, prepend=close[0]) / np.maximum(close, 1e-12)

    valid = ~np.isnan(signal) & ~np.isnan(actual_ret)
    sig = signal[valid]
    act = actual_ret[valid]
    if len(sig) < ret_window + 2:
        return np.nan

    positions = np.sign(sig[:-1])
    strat_ret = positions * act[1:]
    return np.mean(strat_ret) / max(np.std(strat_ret, ddof=1), 1e-12)


def filter_raw(close):
    return close.copy()


def filter_savgol(close):
    return savgol_causal(close, SG_WINDOW, SG_POLY)


def filter_ma(close):
    return pd.Series(close).rolling(SG_WINDOW, min_periods=SG_WINDOW).mean().values


def run_null_model(sigma, n_bars, ret_window, filter_fn, n_sims):
    """Roda N random walks com drift=0, retorna distribuição de SR."""
    srs = []
    for seed in range(n_sims):
        rng = np.random.RandomState(seed)
        rets = sigma * rng.randn(n_bars - 1)
        prices = np.cumprod(np.concatenate([[100.0], 1 + rets]))
        sr = compute_sr(prices, ret_window, filter_fn)
        if not np.isnan(sr):
            srs.append(sr)
    return np.array(srs)


def main():
    print("=" * 70)
    print("  T8 MOD3: Random Walk Null — ret_50 (Raw vs SavGol vs MA)")
    print("=" * 70)

    bars = load_dollar_bars()
    close_real = bars["close"].values.astype(np.float64)
    n_bars = len(close_real)

    # Calibrar sigma das dollar bars reais
    bar_returns = bars["close"].pct_change().dropna().values
    sigma = np.std(bar_returns)
    print(f"  Calibracao: sigma={sigma:.6f}, n_bars={n_bars}")
    print(f"  Simulacoes: {N_SIMS} random walks (drift=0)")
    print()

    filters = {
        "raw": ("ret_50 bruto", filter_raw),
        "savgol": (f"ret_50 SavGol(w={SG_WINDOW})", filter_savgol),
        "ma": (f"ret_50 MA({SG_WINDOW})", filter_ma),
    }

    results = {}

    print(f"  {'Filtro':<25s} {'SR_real':>10s} {'SR_null_mean':>12s} "
          f"{'SR_null_P95':>12s} {'p-value':>10s} {'Veredito':<12s}")
    print(f"  {'-' * 85}")

    for key, (label, fn) in filters.items():
        # SR real
        sr_real = compute_sr(close_real, RET_WINDOW, fn)

        # Null distribution
        sr_null = run_null_model(sigma, n_bars, RET_WINDOW, fn, N_SIMS)

        p5, p50, p95 = np.percentile(sr_null, [5, 50, 95])
        pvalue = float(np.mean(sr_null >= sr_real))
        verdict = "GENUINO" if pvalue < 0.05 else "ARTEFATO"

        results[key] = {
            "label": label,
            "sr_real": sr_real,
            "sr_null": sr_null,
            "sr_null_mean": float(np.mean(sr_null)),
            "sr_null_std": float(np.std(sr_null)),
            "p5": p5, "p50": p50, "p95": p95,
            "pvalue": pvalue,
            "verdict": verdict,
        }

        print(f"  {label:<25s} {sr_real:>10.4f} {np.mean(sr_null):>12.4f} "
              f"{p95:>12.4f} {pvalue:>10.4f} {verdict:<12s}")

    # Autocorrelação do feature (para diagnóstico)
    print(f"\n  Autocorrelacao lag-1 do feature (dados reais):")
    for key, (label, fn) in filters.items():
        close_f = fn(close_real)
        signal = pd.Series(close_f).pct_change(RET_WINDOW).dropna().values
        ac1 = np.corrcoef(signal[:-1], signal[1:])[0, 1]
        print(f"    {label:<25s} AC1 = {ac1:.4f}")

    # Plot: 3 histogramas (um por filtro)
    fig, axes = plt.subplots(1, 3, figsize=(18, 5))
    for ax, (key, res) in zip(axes, results.items()):
        sr_null = res["sr_null"]
        ax.hist(sr_null, bins=40, alpha=0.7, color="steelblue", edgecolor="white",
                label=f"Null (N={len(sr_null)})")
        ax.axvline(res["sr_real"], color="red", lw=2.5, ls="--",
                   label=f"SR real = {res['sr_real']:.4f}")
        ax.axvline(res["p95"], color="orange", lw=1.5, ls=":",
                   label=f"P95 = {res['p95']:.4f}")
        color = "#27ae60" if res["verdict"] == "GENUINO" else "#e74c3c"
        ax.set_title(f"{res['label']}\np={res['pvalue']:.4f} → {res['verdict']}",
                     fontsize=11, fontweight="bold", color=color)
        ax.set_xlabel("Sharpe Ratio (per-bar)")
        ax.legend(fontsize=8)
        ax.grid(True, alpha=0.3)

    fig.suptitle(f"T8 Mod3: sign(ret_50) vs {N_SIMS} Random Walks (drift=0)",
                 fontsize=13, fontweight="bold")
    plt.tight_layout()
    plot_path = os.path.join(SAVE_DIR, "t8_mod3_ret50_null.png")
    fig.savefig(plot_path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"\n  Plot salvo: {plot_path}")

    # TXT report
    txt = "T8 MOD3: RANDOM WALK NULL MODEL — ret_50\n"
    txt += "=" * 60 + "\n\n"
    txt += f"  Configuracao: {N_SIMS} random walks, drift=0, sigma={sigma:.6f}\n"
    txt += f"  Dollar bars: {n_bars} (~20/dia), ret_window={RET_WINDOW}\n\n"

    for key, res in results.items():
        txt += f"  [{res['label']}]\n"
        txt += f"    SR real:      {res['sr_real']:.6f}\n"
        txt += f"    SR null mean: {res['sr_null_mean']:.6f} +/- {res['sr_null_std']:.6f}\n"
        txt += f"    P5 / P50 / P95: {res['p5']:.6f} / {res['p50']:.6f} / {res['p95']:.6f}\n"
        txt += f"    p-value:      {res['pvalue']:.4f}\n"
        txt += f"    Veredito:     {res['verdict']}\n\n"

    txt += "  CONCLUSAO:\n"
    verdicts = {k: v["verdict"] for k, v in results.items()}
    if verdicts["raw"] == "GENUINO":
        txt += "  ret_50 bruto e GENUINO — momentum de ~2.5 dias tem alpha real.\n"
        txt += "  Filtros (SavGol/MA) sao opcionais (suavizacao, nao fonte de alpha).\n"
    elif verdicts["savgol"] == "GENUINO" and verdicts["raw"] == "ARTEFATO":
        txt += "  ret_50 bruto e ARTEFATO, mas SavGol e GENUINO.\n"
        txt += "  O filtro extrai sinal que o retorno bruto nao captura (improvavel).\n"
    elif all(v == "ARTEFATO" for v in verdicts.values()):
        txt += "  TODAS as variantes sao ARTEFATO.\n"
        txt += "  sign(ret_50) nao tem alpha distinguivel de random walk.\n"
        txt += "  O SR positivo e explicado pela autocorrelacao feature→label.\n"
    else:
        txt += f"  Resultados mistos: {verdicts}\n"

    report_path = os.path.join(SCRIPT_DIR, "relatorios", "t8_mod3_ret50.txt")
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(txt)
    print(f"  Report salvo: {report_path}")


if __name__ == "__main__":
    main()
