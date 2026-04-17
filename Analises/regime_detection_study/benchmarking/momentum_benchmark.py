"""
Momentum Benchmark — sign(ret_20) vs Pipeline Completo
=======================================================

Teste direto: a estratégia sign(ret_20) — compra se ret_20 > 0, vende se
ret_20 < 0 — reproduz o alpha do pipeline RF + Meta-Labeling?

  • Se retorno ≈ Mod5 (+54%): o pipeline é momentum com overhead
  • Se retorno << Mod5 (ex: +10-20%): o RF extrai informação não-linear
  • Se retorno < 0: o modelo usa ret_20 de forma não-trivial

Replica EXATAMENTE a mesma infraestrutura do pipeline principal:
  - Dollar bars (mesma calibração, mesmo threshold)
  - Savitzky-Golay causal (mesma janela, mesmo polyorder)
  - ret_20 = pct_change(20) sobre close filtrado
  - Fees pessimistas (taker ambas pontas)
  - Retorno composto sobre close-to-close das dollar bars

Uso:
  python momentum_benchmark.py
"""

import os
import numpy as np
import pandas as pd
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from utils.savgol import savgol_causal
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

# ═══════════════════════════════════════════════════════════════════
# CONFIGURAÇÃO — edite aqui
# ═══════════════════════════════════════════════════════════════════
DATA_DIR = "../data"                   # pasta com btcusdt_1m.csv (treino: ~4.5 anos)
NEW_DATA_DIR = "../new_data"           # pasta com btcusdt_1m.csv (OOS: ago/2025-mar/2026)
SAVE_DIR = "save_point_benchmark"      # saída de gráficos e relatório

DOLLAR_BARS_PER_DAY = 10               # igual ao pipeline
CALIBRATION_DAYS = 30                  # dias para calibrar threshold

SAVGOL_WINDOW = 21                     # janela do filtro SG
SAVGOL_POLYORDER = 3                   # ordem do polinômio

RET_WINDOW = 20                        # janela do retorno (barras)

FEE_TAKER = 0.0270 / 100              # 0.0270% Binance USDT-M
FEE_MODE = "pessimistic"               # taker ambas pontas

# Variantes de benchmark a testar
BENCHMARKS = {
    "sign_ret20":       {"window": 20, "savgol": True},
    "sign_ret20_raw":   {"window": 20, "savgol": False},   # sem filtro SG
    "sign_ret10":       {"window": 10, "savgol": True},
    "sign_ret60":       {"window": 60, "savgol": True},
}


# ═══════════════════════════════════════════════════════════════════
# DOLLAR BARS — réplica exata do pipeline
# ═══════════════════════════════════════════════════════════════════
def build_dollar_bars(df: pd.DataFrame) -> pd.DataFrame:
    """Converte 1-min bars → Dollar Bars (mesma lógica do pipeline)."""
    # Calibrar threshold nos primeiros N dias
    tmp = df.copy()
    tmp["date"] = pd.to_datetime(tmp["timestamp"]).dt.date
    tmp["dollar_vol"] = (
        (tmp["high"] + tmp["low"] + tmp["close"]) / 3.0 * tmp["volume"]
    )
    daily = tmp.groupby("date")["dollar_vol"].sum()
    daily_cal = daily.iloc[:CALIBRATION_DAYS]
    threshold = daily_cal.median() / DOLLAR_BARS_PER_DAY
    print(f"  Dollar bar threshold: ${threshold:,.0f}")

    # Construir barras
    typical_price = (
        df["high"].values + df["low"].values + df["close"].values
    ) / 3.0
    volume = df["volume"].values
    dollar_vol = typical_price * volume
    cum_dollar = np.cumsum(dollar_vol)

    n_bars_max = int(cum_dollar[-1] / threshold) + 1
    thresholds = np.arange(1, n_bars_max + 1) * threshold
    boundary_indices = np.searchsorted(cum_dollar, thresholds, side="right")
    boundary_indices = np.unique(boundary_indices)
    boundary_indices = boundary_indices[boundary_indices < len(df)]
    boundary_indices = boundary_indices[boundary_indices > 0]

    bar_id = np.zeros(len(df), dtype=np.int64)
    prev = 0
    for i, bnd in enumerate(boundary_indices):
        bar_id[prev:bnd] = i
        prev = bnd
    bar_id[prev:] = -1

    tmp2 = pd.DataFrame(
        {
            "bar_id": bar_id,
            "timestamp": df["timestamp"].values,
            "open": df["open"].values,
            "high": df["high"].values,
            "low": df["low"].values,
            "close": df["close"].values,
            "volume": volume,
            "dollar_vol": dollar_vol,
        }
    )
    tmp2 = tmp2[tmp2["bar_id"] >= 0]

    bars = tmp2.groupby("bar_id").agg(
        timestamp=("timestamp", "first"),
        open=("open", "first"),
        high=("high", "max"),
        low=("low", "min"),
        close=("close", "last"),
        volume=("volume", "sum"),
        dollar_volume=("dollar_vol", "sum"),
        tick_count=("bar_id", "count"),
    )
    bars["vwap"] = bars["dollar_volume"] / bars["volume"].replace(0, np.nan)
    bars = bars.reset_index(drop=True)
    print(f"  Dollar bars construídas: {len(bars)}")
    return bars


# savgol_causal imported from utils.savgol (canonical, edge-padded version)


# ═══════════════════════════════════════════════════════════════════
# COMPUTE STRATEGY RETURNS — réplica exata (com fees)
# ═══════════════════════════════════════════════════════════════════
def compute_strategy_returns(
    predictions: np.ndarray,
    actual_returns: np.ndarray,
    fee_taker: float = 0.0,
    fee_mode: str = "pessimistic",
) -> np.ndarray:
    """pred × actual_return − custos de transação por mudança de posição."""
    raw = predictions * actual_returns
    if fee_taker == 0.0:
        return raw

    if fee_mode == "pessimistic":
        fee_entry = fee_taker
        fee_exit = fee_taker
    else:
        fee_entry = fee_taker
        fee_exit = fee_taker * (0.0090 / 0.0270)  # maker

    costs = np.zeros_like(raw)
    prev = 0.0
    for i in range(len(predictions)):
        cur = predictions[i]
        if cur != prev:
            if prev != 0:
                costs[i] += fee_exit
            if cur != 0:
                costs[i] += fee_entry
        prev = cur
    return raw - costs


# ═══════════════════════════════════════════════════════════════════
# BENCHMARK PRINCIPAL
# ═══════════════════════════════════════════════════════════════════
def run_benchmark(bars: pd.DataFrame, name: str, cfg: dict) -> dict:
    """Roda um benchmark sign(ret_N) e retorna métricas."""
    close = bars["close"].values.astype(np.float64)
    window = cfg["window"]

    # Calcular ret_N
    if cfg["savgol"]:
        close_filtered = savgol_causal(close, SAVGOL_WINDOW, SAVGOL_POLYORDER)
    else:
        close_filtered = close.copy()

    close_series = pd.Series(close_filtered)
    ret_n = close_series.pct_change(window).values

    # Sinal: sign(ret_N)
    predictions = np.sign(ret_n)
    predictions = np.nan_to_num(predictions, nan=0.0)

    # Retornos reais (close-to-close, mesma fórmula do pipeline)
    actual_ret = np.diff(close, prepend=close[0]) / np.maximum(close, 1e-12)

    # Estratégia com fees
    strat_ret = compute_strategy_returns(predictions, actual_ret, FEE_TAKER, FEE_MODE)

    # Buy & Hold
    bh_ret = actual_ret.copy()

    # Retornos compostos
    strat_equity = np.cumprod(1 + strat_ret)
    bh_equity = np.cumprod(1 + bh_ret)

    strat_total = strat_equity[-1] - 1
    bh_total = bh_equity[-1] - 1

    # Trades ativos e custos
    n_active = int(np.sum(predictions != 0))
    position_changes = np.sum(np.diff(predictions) != 0)

    # Sharpe (apenas trades ativos)
    active_mask = predictions != 0
    active_returns = strat_ret[active_mask]
    if len(active_returns) > 1 and np.std(active_returns) > 0:
        sharpe_active = np.mean(active_returns) / np.std(active_returns)
    else:
        sharpe_active = 0.0

    # Sharpe todas barras
    if np.std(strat_ret) > 0:
        sharpe_all = np.mean(strat_ret) / np.std(strat_ret)
    else:
        sharpe_all = 0.0

    # Dias no período
    ts = pd.to_datetime(bars["timestamp"])
    n_days = (ts.iloc[-1] - ts.iloc[0]).total_seconds() / 86400

    return {
        "name": name,
        "window": window,
        "savgol": cfg["savgol"],
        "n_bars": len(bars),
        "n_days": n_days,
        "n_active": n_active,
        "pct_active": n_active / len(bars) * 100,
        "position_changes": int(position_changes),
        "strat_total": strat_total,
        "bh_total": bh_total,
        "alpha_vs_bh": strat_total - bh_total,
        "sharpe_all": sharpe_all,
        "sharpe_active": sharpe_active,
        "strat_equity": strat_equity,
        "bh_equity": bh_equity,
        "predictions": predictions,
        "strat_ret": strat_ret,
    }


# ═══════════════════════════════════════════════════════════════════
# RELATÓRIO E GRÁFICOS
# ═══════════════════════════════════════════════════════════════════
def print_report(results: list[dict]):
    """Imprime relatório comparativo."""
    print("\n" + "=" * 70)
    print("MOMENTUM BENCHMARK — sign(ret_N) vs Pipeline Completo")
    print("=" * 70)

    # Referências dos modelos do pipeline
    refs = {
        "Mod5 (RF+Meta, fees)": "+54.02%",
        "Mod4 (RF+Meta, sem fees)": "+114.71%",
        "Mod3 (RF+Meta, sem fees)": "+33.03%",
        "BTC B&H": None,
    }

    print(f"\n  {'Estratégia':<28} {'Retorno':>10} {'Alpha/BTC':>12} "
          f"{'SR(all)':>10} {'SR(active)':>12} {'Trades':>8} {'%Ativo':>8}")
    print("  " + "-" * 90)

    for r in results:
        print(
            f"  {r['name']:<28} {r['strat_total']:>+10.2%} "
            f"{r['alpha_vs_bh']:>+12.2%} "
            f"{r['sharpe_all']:>10.4f} {r['sharpe_active']:>12.4f} "
            f"{r['position_changes']:>8d} {r['pct_active']:>7.1f}%"
        )

    bh_total = results[0]["bh_total"]
    print(f"  {'BTC Buy & Hold':<28} {bh_total:>+10.2%} {'—':>12}")

    print("\n  Referências do pipeline (mesmo período OOS):")
    for name, ret in refs.items():
        if ret:
            print(f"    {name}: {ret}")

    print(f"\n  Fees: taker = {FEE_TAKER*100:.4f}% | mode = {FEE_MODE}")
    print(f"  Período: {results[0]['n_days']:.1f} dias | {results[0]['n_bars']} dollar bars")


def _save(fig: plt.Figure, name: str):
    path = os.path.join(SAVE_DIR, name)
    fig.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"    Plot salvo: {path}")


def plot_portfolio_equity(r: dict, bars: pd.DataFrame, suffix: str = ""):
    """
    Rentabilidade REAL composta: estrategia vs BTC buy & hold.
    Replica o estilo de portfolio_equity.png do pipeline.
    """
    timestamps = pd.to_datetime(bars["timestamp"])
    close = bars["close"].values.astype(np.float64)

    equity_strat = r["strat_equity"]
    equity_btc = close / close[0]

    # Max drawdown
    running_max = np.maximum.accumulate(equity_strat)
    drawdowns = (equity_strat - running_max) / running_max
    max_dd = drawdowns.min()

    ret_strat = (equity_strat[-1] - 1.0) * 100
    ret_btc = (equity_btc[-1] - 1.0) * 100

    fig, ax = plt.subplots(figsize=(14, 7))
    ax.plot(timestamps, equity_strat, label="Estrategia sign(ret)",
            lw=1.5, color="blue")
    ax.plot(timestamps, equity_btc, label="BTC Buy & Hold",
            lw=1.2, color="orange", alpha=0.8)
    ax.axhline(1.0, color="gray", ls=":", lw=0.8, alpha=0.5)
    ax.fill_between(timestamps, equity_strat, 1.0, alpha=0.08, color="blue")

    txt = (
        f"Estrategia: {ret_strat:+.2f}%\n"
        f"BTC B&H:    {ret_btc:+.2f}%\n"
        f"Max DD:     {max_dd * 100:.2f}%\n"
        f"SR: {r['sharpe_all']:.4f}\n"
        f"SR(active): {r['sharpe_active']:.4f}"
    )
    ax.text(0.02, 0.95, txt, transform=ax.transAxes, fontsize=10,
            verticalalignment="top", family="monospace",
            bbox=dict(boxstyle="round", facecolor="wheat", alpha=0.7))

    ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m-%d"))
    fig.autofmt_xdate()
    ax.set_xlabel("Data")
    ax.set_ylabel("Valor do Portfolio (1.0 = capital inicial)")
    ax.set_title(f"Portfolio Equity: {r['name']} (fees pessimistas)")
    ax.legend(fontsize=9, loc="lower right")
    ax.grid(True, alpha=0.3)
    plt.tight_layout()
    fname = f"portfolio_equity{suffix}.png" if suffix else f"portfolio_equity_{r['name']}.png"
    _save(fig, fname)


def plot_cumulative_returns(r: dict, suffix: str = ""):
    """
    Retorno acumulado (soma aritmetica) — replica cumulative_returns.png.
    """
    strat_ret = r["strat_ret"]
    actual_ret = r["bh_equity"] / np.concatenate([[1.0], r["bh_equity"][:-1]]) - 1.0

    cum_strat = np.cumsum(strat_ret)
    cum_bench = np.cumsum(actual_ret)

    fig, ax = plt.subplots(figsize=(14, 6))
    ax.plot(cum_strat, label="Estrategia sign(ret)", lw=1.2, color="blue")
    ax.plot(cum_bench, label="BTC Buy & Hold", lw=1.0, color="orange", alpha=0.7)
    ax.axhline(0, color="gray", ls=":", lw=0.8)
    ax.fill_between(range(len(cum_strat)), cum_strat, alpha=0.1, color="blue")

    txt = f"SR(all) = {r['sharpe_all']:.4f}\nSR(active) = {r['sharpe_active']:.4f}"
    ax.text(0.02, 0.95, txt, transform=ax.transAxes, fontsize=11,
            verticalalignment="top",
            bbox=dict(boxstyle="round", facecolor="wheat", alpha=0.5))

    ax.set_xlabel("Indice da Barra")
    ax.set_ylabel("Retorno Acumulado")
    ax.set_title(f"Retorno Acumulado Aritmetico: {r['name']}")
    ax.legend(fontsize=9)
    ax.grid(True, alpha=0.3)
    plt.tight_layout()
    fname = f"cumulative_returns{suffix}.png" if suffix else f"cumulative_returns_{r['name']}.png"
    _save(fig, fname)


def plot_return_distribution(r: dict, suffix: str = ""):
    """
    Histograma de retornos por barra (trades ativos).
    Replica o estilo do cpcv_sharpe_distribution.png.
    """
    active_ret = r["strat_ret"][r["predictions"] != 0]
    if len(active_ret) == 0:
        return

    mean_r = np.mean(active_ret)
    std_r = np.std(active_ret)
    skew = float(pd.Series(active_ret).skew())
    kurt = float(pd.Series(active_ret).kurtosis())

    fig, ax = plt.subplots(figsize=(10, 6))
    ax.hist(active_ret * 100, bins=max(20, len(active_ret) // 20),
            edgecolor="black", alpha=0.7, color="#3498db", linewidth=0.5)
    ax.axvline(mean_r * 100, color="red", ls="--", lw=2,
               label=f"Media={mean_r * 100:.4f}%")
    ax.axvline(0, color="gray", ls=":", lw=1)

    txt = (
        f"N trades = {len(active_ret)}\n"
        f"Media = {mean_r * 100:.4f}%\n"
        f"Std = {std_r * 100:.4f}%\n"
        f"Skew = {skew:.3f}\n"
        f"Kurt = {kurt:.3f}\n"
        f"SR = {r['sharpe_active']:.4f}"
    )
    ax.text(0.98, 0.95, txt, transform=ax.transAxes, fontsize=11,
            verticalalignment="top", horizontalalignment="right",
            family="monospace",
            bbox=dict(boxstyle="round", facecolor="wheat", alpha=0.5))

    ax.set_xlabel("Retorno por Trade (%)")
    ax.set_ylabel("Frequencia")
    ax.set_title(f"Distribuicao de Retornos — {r['name']} (trades ativos)")
    ax.legend()
    plt.tight_layout()
    fname = f"return_distribution{suffix}.png" if suffix else f"return_distribution_{r['name']}.png"
    _save(fig, fname)


def plot_results(results: list[dict], bars: pd.DataFrame):
    """Gera todos os gráficos."""
    os.makedirs(SAVE_DIR, exist_ok=True)

    # --- 1. Portfolio equity individual para cada benchmark ---
    for r in results:
        plot_portfolio_equity(r, bars)
        plot_cumulative_returns(r)
        plot_return_distribution(r)

    # --- 2. Equity curves sobrepostas (comparativo) ---
    ts = pd.to_datetime(bars["timestamp"])
    close = bars["close"].values.astype(np.float64)

    fig, ax = plt.subplots(figsize=(14, 7))
    colors = ["#2196F3", "#FF9800", "#4CAF50", "#9C27B0"]
    for idx, r in enumerate(results):
        ax.plot(ts, r["strat_equity"],
                label=f"{r['name']} ({r['strat_total']:+.2%})",
                linewidth=1.2, color=colors[idx % len(colors)])
    ax.plot(ts, close / close[0],
            label=f"BTC B&H ({results[0]['bh_total']:+.2%})",
            color="gray", linewidth=1.2, linestyle="--")
    ax.axhline(1.0, color="black", linewidth=0.5, linestyle=":")
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m-%d"))
    fig.autofmt_xdate()
    ax.set_title("Momentum Benchmark — Equity Curves Comparativo (fees pessimistas)")
    ax.set_ylabel("Equity (base 1.0)")
    ax.set_xlabel("Data")
    ax.legend(loc="best", fontsize=9)
    ax.grid(True, alpha=0.3)
    plt.tight_layout()
    _save(fig, "equity_curves_all.png")

    # --- 3. Barplot comparativo ---
    fig, axes = plt.subplots(1, 3, figsize=(16, 5))

    names = [r["name"] for r in results]
    returns = [r["strat_total"] * 100 for r in results]
    sharpes = [r["sharpe_active"] for r in results]
    alphas = [r["alpha_vs_bh"] * 100 for r in results]

    ax = axes[0]
    ax.bar(names, returns, color=colors[: len(names)])
    ax.axhline(54.02, color="red", linestyle="--", linewidth=1, label="Mod5 (+54.02%)")
    ax.axhline(0, color="black", linewidth=0.5)
    ax.set_ylabel("Retorno (%)")
    ax.set_title("Retorno Total")
    ax.legend(fontsize=8)
    ax.tick_params(axis="x", rotation=30)

    ax = axes[1]
    ax.bar(names, sharpes, color=colors[: len(names)])
    ax.axhline(0.142, color="red", linestyle="--", linewidth=1, label="Mod5 (0.142)")
    ax.axhline(0, color="black", linewidth=0.5)
    ax.set_ylabel("Sharpe Ratio")
    ax.set_title("Sharpe (trades ativos)")
    ax.legend(fontsize=8)
    ax.tick_params(axis="x", rotation=30)

    ax = axes[2]
    ax.bar(names, alphas, color=colors[: len(names)])
    ax.axhline(88.30, color="red", linestyle="--", linewidth=1, label="Mod5 (+88.30pp)")
    ax.axhline(0, color="black", linewidth=0.5)
    ax.set_ylabel("Alpha vs BTC (pp)")
    ax.set_title("Alpha vs Buy & Hold")
    ax.legend(fontsize=8)
    ax.tick_params(axis="x", rotation=30)

    fig.suptitle("sign(ret_N) vs Pipeline RF+Meta-Labeling", fontsize=13, fontweight="bold")
    fig.tight_layout()
    _save(fig, "benchmark_comparison.png")

    print(f"\n  Graficos salvos em {SAVE_DIR}/")


def save_report(results: list[dict]):
    """Salva relatório em texto."""
    os.makedirs(SAVE_DIR, exist_ok=True)
    lines = []
    lines.append("MOMENTUM BENCHMARK REPORT")
    lines.append("=" * 60)
    lines.append("")
    lines.append(f"  Fees: taker = {FEE_TAKER*100:.4f}% | mode = {FEE_MODE}")
    lines.append(f"  Período: {results[0]['n_days']:.1f} dias | {results[0]['n_bars']} dollar bars")
    lines.append(f"  BTC B&H: {results[0]['bh_total']:+.2%}")
    lines.append("")

    for r in results:
        lines.append(f"  {r['name']}:")
        lines.append(f"    Janela: {r['window']} barras | SavGol: {r['savgol']}")
        lines.append(f"    Retorno: {r['strat_total']:+.4%}")
        lines.append(f"    Alpha vs BTC: {r['alpha_vs_bh']:+.4%}")
        lines.append(f"    Sharpe (all): {r['sharpe_all']:.6f}")
        lines.append(f"    Sharpe (active): {r['sharpe_active']:.6f}")
        lines.append(f"    Trades ativos: {r['n_active']} ({r['pct_active']:.1f}%)")
        lines.append(f"    Mudanças de posição: {r['position_changes']}")
        lines.append("")

    lines.append("  Referências pipeline (mesmo OOS):")
    lines.append("    Mod5 (RF+Meta, fees pess.): +54.02%  | SR(active): 0.142")
    lines.append("    Mod4 (RF+Meta, sem fees):    +114.71% | SR(active): 0.142")
    lines.append("    Mod3 (RF+Meta, sem fees):    +33.03%  | SR(active): 0.191")
    lines.append("")

    path = os.path.join(SAVE_DIR, "benchmark_report.txt")
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    print(f"  Relatório salvo em {path}")


# ═══════════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════════
def run_dataset(label: str, btc_path: str, save_suffix: str):
    """Roda o benchmark completo sobre um dataset."""
    global SAVE_DIR
    script_dir = os.path.dirname(os.path.abspath(__file__))
    original_save = SAVE_DIR
    SAVE_DIR = os.path.join(script_dir, original_save, save_suffix)
    os.makedirs(SAVE_DIR, exist_ok=True)

    print(f"\n{'='*70}")
    print(f"  DATASET: {label}")
    print(f"{'='*70}")

    print(f"\n[1] Carregando dados de {btc_path}")
    btc_df = pd.read_csv(btc_path, parse_dates=["timestamp"])
    print(f"  Linhas 1-min: {len(btc_df):,}")

    print("\n[2] Construindo dollar bars")
    bars = build_dollar_bars(btc_df)

    print("\n[3] Rodando benchmarks")
    results = []
    for name, cfg in BENCHMARKS.items():
        print(f"  > {name} (window={cfg['window']}, savgol={cfg['savgol']})")
        r = run_benchmark(bars, name, cfg)
        results.append(r)

    print_report(results)
    save_report(results)
    plot_results(results, bars)

    # Veredicto
    main_ret = results[0]["strat_total"]
    print(f"\n{'='*70}")
    print(f"VEREDICTO — {label}")
    print(f"{'='*70}")
    if main_ret > 0.40:
        print("  sign(ret_20) >= Mod5 -> pipeline e essencialmente MOMENTUM")
        print("  O RF + Meta-Labeling adiciona pouco valor sobre sign(ret_20)")
    elif main_ret > 0.10:
        print("  sign(ret_20) captura parte do alpha, mas o pipeline agrega valor")
        print("  O RF extrai informacao nao-linear que sign() nao capta")
    elif main_ret > 0:
        print("  sign(ret_20) captura alpha marginal -- pipeline agrega MUITO valor")
        print("  O meta-labeling e o timing sao a fonte real do alpha")
    else:
        print("  sign(ret_20) e NEGATIVO -> o modelo usa ret_20 de forma NAO-TRIVIAL")
        print("  A direcao bruta do momentum NAO e a estrategia; o RF faz algo mais complexo")
    print("=" * 70)

    SAVE_DIR = original_save
    return results


def main():
    script_dir = os.path.dirname(os.path.abspath(__file__))

    print("MOMENTUM BENCHMARK")
    print("=" * 60)

    # --- Dataset OOS (bear market, mesmo periodo do Mod5) ---
    oos_path = os.path.join(script_dir, NEW_DATA_DIR, "btcusdt_1m.csv")
    if os.path.exists(oos_path):
        run_dataset(
            "OOS Bear Market (ago/2025 - mar/2026) — comparavel ao Mod5",
            oos_path,
            "oos",
        )
    else:
        print(f"\n  [AVISO] {oos_path} nao encontrado, pulando OOS")

    # --- Dataset treino (4.5 anos, in-sample) ---
    train_path = os.path.join(script_dir, DATA_DIR, "btcusdt_1m.csv")
    if os.path.exists(train_path):
        run_dataset(
            "Treino/Full (4.5 anos) — referencia in-sample",
            train_path,
            "full",
        )


if __name__ == "__main__":
    main()
