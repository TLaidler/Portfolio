#!/usr/bin/env python3
# coding: utf-8
"""
=============================================================================
Aplicacao do Modelo Treinado em Novos Dados — BTC/USDT Regime Detection
=============================================================================

Carrega o modelo treinado por regime_detection_advanced.py e aplica a um
novo dataset com a mesma estrutura. Gera plots diagnosticos e relatorios.

Uso:
  1. Rode regime_detection_advanced.py para gerar trained_model.joblib
  2. Coloque seus dados em new_data/ (btcusdt_1m.csv + fear_greed.csv)
  3. Execute: python rd_adv_application.py
  4. Resultados em save_point_application/
"""

import os
import sys
import warnings

import joblib
import numpy as np
import pandas as pd
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from scipy import stats as sp_stats
from sklearn.metrics import (
    accuracy_score,
    f1_score,
    classification_report,
    confusion_matrix as sk_confusion_matrix,
)

# Importar classes do pipeline de treino (evitar duplicacao)
from regime_detection_advanced import (
    DollarBarBuilder,
    FeatureRegistry,
    TripleBarrierLabeler,
    MetaLabeler,
    ModelEvaluator,
    DEFAULT_CONFIG,
)


# ===========================================================================
# VISUALIZACOES — especificas para aplicacao
# ===========================================================================
class ApplicationVisualizer:
    """Gera plots diagnosticos para aplicacao do modelo em novos dados."""

    def __init__(self, save_dir: str):
        self.save_dir = save_dir

    def _save(self, fig: plt.Figure, name: str) -> None:
        path = os.path.join(self.save_dir, name)
        fig.savefig(path, dpi=150, bbox_inches="tight")
        plt.close(fig)
        print(f"    Plot salvo: {path}")

    def plot_regime_classification(
        self,
        timestamps: np.ndarray,
        close: np.ndarray,
        predictions: np.ndarray,
        primary_preds: np.ndarray,
    ) -> None:
        """Preco ao longo do tempo com regimes coloridos."""
        timestamps = pd.to_datetime(timestamps)
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(16, 10), sharex=True)

        # Plot 1: Predicoes finais (meta-label)
        ax1.plot(timestamps, close, color="gray", lw=0.5, alpha=0.6)
        colors = {1: "green", -1: "red", 0: "gold"}
        labels_map = {1: "Bull (+1)", -1: "Bear (-1)", 0: "Neutro (0)"}
        for regime in [1, -1, 0]:
            mask = predictions == regime
            if mask.any():
                ax1.scatter(
                    timestamps[mask], close[mask],
                    c=colors[regime], s=3, alpha=0.5,
                    label=labels_map[regime],
                )
        ax1.set_ylabel("Preco (USD)")
        ax1.set_title("Regimes Detectados — Predicao Final (Meta-Label)")
        ax1.legend(fontsize=8, loc="upper left")
        ax1.grid(True, alpha=0.3)

        # Plot 2: Predicoes primarias (sem filtro meta)
        ax2.plot(timestamps, close, color="gray", lw=0.5, alpha=0.6)
        for regime in [1, -1]:
            mask = primary_preds == regime
            if mask.any():
                ax2.scatter(
                    timestamps[mask], close[mask],
                    c=colors[regime], s=3, alpha=0.5,
                    label=labels_map[regime],
                )
        ax2.set_ylabel("Preco (USD)")
        ax2.set_xlabel("Data")
        ax2.set_title("Regimes Detectados — Predicao Primaria (sem filtro)")
        ax2.legend(fontsize=8, loc="upper left")
        ax2.grid(True, alpha=0.3)

        ax2.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m-%d"))
        fig.autofmt_xdate()
        plt.tight_layout()
        self._save(fig, "regime_classification.png")

    def plot_triple_barrier_labels(
        self,
        timestamps: np.ndarray,
        close: np.ndarray,
        labels: np.ndarray,
    ) -> None:
        """Preco com labels do triple-barrier (ground truth)."""
        timestamps = pd.to_datetime(timestamps)
        fig, ax = plt.subplots(figsize=(14, 7))
        ax.plot(timestamps, close, color="gray", lw=0.5, alpha=0.6)
        colors = {1: "green", -1: "red", 0: "gold"}
        labels_map = {1: "Profit-Take (+1)", -1: "Stop-Loss (-1)", 0: "Vertical (0)"}
        for label_val in [1, -1, 0]:
            mask = labels == label_val
            if mask.any():
                ax.scatter(
                    timestamps[mask], close[mask],
                    c=colors[label_val], s=3, alpha=0.5,
                    label=labels_map[label_val],
                )
        ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m-%d"))
        fig.autofmt_xdate()
        ax.set_xlabel("Data")
        ax.set_ylabel("Preco (USD)")
        ax.set_title("Triple-Barrier Labels (Ground Truth)")
        ax.legend(fontsize=8, loc="upper left")
        ax.grid(True, alpha=0.3)
        plt.tight_layout()
        self._save(fig, "triple_barrier_labels.png")

    def plot_portfolio_equity(
        self,
        strategy_returns: np.ndarray,
        close_prices: np.ndarray,
        timestamps: np.ndarray,
        sharpe: float,
        psr: float,
        dsr: float,
    ) -> None:
        """Rentabilidade real composta: estrategia vs BTC buy & hold."""
        timestamps = pd.to_datetime(timestamps)
        equity_strat = np.cumprod(1.0 + strategy_returns)
        equity_btc = close_prices / close_prices[0]

        running_max = np.maximum.accumulate(equity_strat)
        drawdowns = (equity_strat - running_max) / running_max
        max_dd = drawdowns.min()

        ret_strat = (equity_strat[-1] - 1.0) * 100
        ret_btc = (equity_btc[-1] - 1.0) * 100

        fig, ax = plt.subplots(figsize=(14, 7))
        ax.plot(timestamps, equity_strat, label="Estrategia (Meta-Label)", lw=1.5, color="blue")
        ax.plot(timestamps, equity_btc, label="BTC Buy & Hold", lw=1.2, color="orange", alpha=0.8)
        ax.axhline(1.0, color="gray", ls=":", lw=0.8, alpha=0.5)
        ax.fill_between(timestamps, equity_strat, 1.0, alpha=0.08, color="blue")

        txt = (
            f"Estrategia: {ret_strat:+.2f}%\n"
            f"BTC B&H:    {ret_btc:+.2f}%\n"
            f"Max DD:     {max_dd * 100:.2f}%\n"
            f"SR: {sharpe:.4f}\n"
            f"PSR: {psr:.4f}  DSR: {dsr:.4f}"
        )
        ax.text(
            0.02, 0.95, txt, transform=ax.transAxes, fontsize=10,
            verticalalignment="top", family="monospace",
            bbox=dict(boxstyle="round", facecolor="wheat", alpha=0.7),
        )
        ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m-%d"))
        fig.autofmt_xdate()
        ax.set_xlabel("Data")
        ax.set_ylabel("Valor do Portfolio (1.0 = capital inicial)")
        ax.set_title("Rentabilidade Real: Estrategia vs BTC/USDT (novos dados)")
        ax.legend(fontsize=9, loc="lower right")
        ax.grid(True, alpha=0.3)
        plt.tight_layout()
        self._save(fig, "portfolio_equity.png")

    def plot_portfolio_equity_extended(
        self,
        strategy_returns: np.ndarray,
        close_prices: np.ndarray,
        timestamps: np.ndarray,
        sr: float, psr: float, dsr: float,
        sr_active: float, psr_active: float, dsr_active: float,
        sr_vs_selic: float, psr_vs_selic: float,
        sr_active_vs_selic: float, psr_active_vs_selic: float,
        rf_annual: float, total_days: float, n_active: int,
    ) -> None:
        """Equity curve com US Risk-Free e painel completo de Sharpe."""
        timestamps = pd.to_datetime(timestamps)
        n_bars = len(strategy_returns)
        equity_strat = np.cumprod(1.0 + strategy_returns)
        equity_btc = close_prices / close_prices[0]

        # US Risk-Free equity curve: crescimento diario composto
        days_per_bar = total_days / max(n_bars, 1)
        rf_per_bar = (1.0 + rf_annual) ** (days_per_bar / 365.0) - 1.0
        equity_selic = np.cumprod(np.full(n_bars, 1.0 + rf_per_bar))

        running_max = np.maximum.accumulate(equity_strat)
        drawdowns = (equity_strat - running_max) / running_max
        max_dd = drawdowns.min()

        ret_strat = (equity_strat[-1] - 1.0) * 100
        ret_btc = (equity_btc[-1] - 1.0) * 100
        ret_selic = (equity_selic[-1] - 1.0) * 100

        fig, ax = plt.subplots(figsize=(16, 9))
        ax.plot(timestamps, equity_strat, label="Estrategia (Meta-Label)", lw=1.8, color="blue")
        ax.plot(timestamps, equity_btc, label="BTC Buy & Hold", lw=1.2, color="orange", alpha=0.8)
        ax.plot(timestamps, equity_selic, label=f"US Risk-Free {rf_annual*100:.0f}% a.a.", lw=1.2, color="green", ls="--", alpha=0.8)
        ax.axhline(1.0, color="gray", ls=":", lw=0.8, alpha=0.5)
        ax.fill_between(timestamps, equity_strat, 1.0, alpha=0.08, color="blue")

        txt = (
            f"{'RENTABILIDADE':^40}\n"
            f"{'='*40}\n"
            f"Estrategia: {ret_strat:+.2f}%\n"
            f"BTC B&H:    {ret_btc:+.2f}%\n"
            f"US Risk-Free:      {ret_selic:+.2f}%\n"
            f"Max DD:     {max_dd * 100:.2f}%\n"
            f"Periodo:    {total_days:.1f} dias\n"
            f"\n{'SHARPE (todas barras, c/ abstencoes)':^40}\n"
            f"{'='*40}\n"
            f"SR: {sr:.4f} | PSR: {psr:.4f} | DSR: {dsr:.4f}\n"
            f"\n{'SHARPE (apenas trades ativos: '+str(n_active)+')':^40}\n"
            f"{'='*40}\n"
            f"SR: {sr_active:.4f} | PSR: {psr_active:.4f} | DSR: {dsr_active:.4f}\n"
            f"\n{'SHARPE vs US Risk-Free 4.5% a.a.':^40}\n"
            f"{'='*40}\n"
            f"SR (all):    {sr_vs_selic:.4f} | PSR: {psr_vs_selic:.4f}\n"
            f"SR (active): {sr_active_vs_selic:.4f} | PSR: {psr_active_vs_selic:.4f}"
        )
        ax.text(
            0.02, 0.97, txt, transform=ax.transAxes, fontsize=8,
            verticalalignment="top", family="monospace",
            bbox=dict(boxstyle="round", facecolor="wheat", alpha=0.85),
        )
        ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m-%d"))
        fig.autofmt_xdate()
        ax.set_xlabel("Data")
        ax.set_ylabel("Valor do Portfolio (1.0 = capital inicial)")
        ax.set_title("Rentabilidade: Estrategia vs BTC vs US Risk-Free (novos dados)")
        ax.legend(fontsize=9, loc="lower right")
        ax.grid(True, alpha=0.3)
        plt.tight_layout()
        self._save(fig, "portfolio_equity.png")

    def plot_cumulative_returns(
        self,
        strategy_returns: np.ndarray,
        benchmark_returns: np.ndarray,
        psr: float,
        dsr: float,
    ) -> None:
        """Retorno acumulado (soma aritmetica)."""
        fig, ax = plt.subplots(figsize=(12, 6))
        cum_strat = np.cumsum(strategy_returns)
        cum_bench = np.cumsum(benchmark_returns)
        ax.plot(cum_strat, label="Estrategia (Meta-Label)", lw=1.2, color="blue")
        ax.plot(cum_bench, label="BTC Buy & Hold", lw=1.0, color="orange", alpha=0.7)
        ax.axhline(0, color="gray", ls=":", lw=0.8)
        ax.set_xlabel("Barra (indice)")
        ax.set_ylabel("Retorno acumulado (soma)")
        ax.set_title(f"Retorno Acumulado Aritmetico | PSR={psr:.4f}, DSR={dsr:.4f}")
        ax.legend(fontsize=9)
        ax.grid(True, alpha=0.3)
        plt.tight_layout()
        self._save(fig, "cumulative_returns.png")

    def plot_meta_label_filtering(
        self,
        timestamps: np.ndarray,
        close: np.ndarray,
        primary_preds: np.ndarray,
        final_preds: np.ndarray,
    ) -> None:
        """Trades mantidos vs filtrados pelo meta-labeler."""
        timestamps = pd.to_datetime(timestamps)
        kept = final_preds != 0
        filtered = (primary_preds != 0) & (final_preds == 0)

        fig, ax = plt.subplots(figsize=(14, 7))
        ax.plot(timestamps, close, color="gray", lw=0.5, alpha=0.5)
        if kept.any():
            ax.scatter(
                timestamps[kept], close[kept],
                c="blue", s=4, alpha=0.4, label=f"Mantidos ({kept.sum()})",
            )
        if filtered.any():
            ax.scatter(
                timestamps[filtered], close[filtered],
                c="red", s=4, alpha=0.3, label=f"Filtrados ({filtered.sum()})",
            )

        total_primary = (primary_preds != 0).sum()
        pct_kept = kept.sum() / max(total_primary, 1) * 100
        ax.text(
            0.02, 0.95,
            f"Primario apostou: {total_primary}\n"
            f"Meta manteve: {kept.sum()} ({pct_kept:.1f}%)\n"
            f"Meta filtrou: {filtered.sum()} ({100 - pct_kept:.1f}%)",
            transform=ax.transAxes, fontsize=10, verticalalignment="top",
            family="monospace",
            bbox=dict(boxstyle="round", facecolor="lightyellow", alpha=0.7),
        )
        ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m-%d"))
        fig.autofmt_xdate()
        ax.set_xlabel("Data")
        ax.set_ylabel("Preco (USD)")
        ax.set_title("Meta-Label Filtering: Trades Mantidos vs Filtrados")
        ax.legend(fontsize=9, loc="lower right")
        ax.grid(True, alpha=0.3)
        plt.tight_layout()
        self._save(fig, "meta_label_filtering.png")

    def plot_confusion_matrix(
        self, y_true: np.ndarray, y_pred: np.ndarray
    ) -> None:
        """Matriz de confusao."""
        labels = sorted(set(y_true) | set(y_pred))
        cm = sk_confusion_matrix(y_true, y_pred, labels=labels)
        fig, ax = plt.subplots(figsize=(7, 6))
        im = ax.imshow(cm, interpolation="nearest", cmap=plt.cm.Blues)
        fig.colorbar(im, ax=ax)
        ax.set(
            xticks=range(len(labels)),
            yticks=range(len(labels)),
            xticklabels=labels,
            yticklabels=labels,
            xlabel="Predicao",
            ylabel="Real",
            title="Matriz de Confusao (novos dados)",
        )
        for i in range(len(labels)):
            for j in range(len(labels)):
                color = "white" if cm[i, j] > cm.max() / 2 else "black"
                ax.text(j, i, str(cm[i, j]), ha="center", va="center", color=color)
        plt.tight_layout()
        self._save(fig, "confusion_matrix.png")


# ===========================================================================
# PIPELINE DE APLICACAO
# ===========================================================================
class ApplicationPipeline:
    """Aplica modelo treinado a novos dados."""

    def __init__(
        self,
        model_path: str = "save_point_advanced/trained_model.joblib",
        data_dir: str = "new_data",
        save_dir: str = "save_point_application",
    ):
        self.model_path = model_path
        self.data_dir = data_dir
        self.save_dir = save_dir

    def _save_txt(self, name: str, content: str) -> None:
        path = os.path.join(self.save_dir, name)
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
        print(f"    Relatorio salvo: {path}")

    def run(self) -> dict:
        """Executa o pipeline de aplicacao."""
        script_dir = os.path.dirname(os.path.abspath(__file__))
        save_dir = os.path.join(script_dir, self.save_dir)
        os.makedirs(save_dir, exist_ok=True)
        self.save_dir = save_dir
        viz = ApplicationVisualizer(save_dir)

        # == 1. CARREGAR MODELO TREINADO =====================================
        print("\n" + "=" * 70)
        print("  ETAPA 1: Carregando modelo treinado")
        print("=" * 70)
        model_path = os.path.join(script_dir, self.model_path)
        if not os.path.exists(model_path):
            print(f"    ERRO: Modelo nao encontrado em {model_path}")
            print("    Rode regime_detection_advanced.py primeiro.")
            sys.exit(1)

        artifacts = joblib.load(model_path)
        config = artifacts["config"]
        threshold = artifacts["threshold"]
        selected_features = artifacts["selected_features"]
        feature_names = artifacts["feature_names"]
        meta: MetaLabeler = artifacts["meta_labeler"]

        print(f"    Modelo carregado de: {model_path}")
        print(f"    Threshold: ${threshold:,.0f}")
        print(f"    Features selecionadas: {selected_features}")

        # == 2. CARREGAR NOVOS DADOS =========================================
        print("\n" + "=" * 70)
        print("  ETAPA 2: Carregando novos dados")
        print("=" * 70)
        data_dir = os.path.join(script_dir, self.data_dir)

        btc_path = os.path.join(data_dir, "btcusdt_1m.csv")
        if not os.path.exists(btc_path):
            print(f"    ERRO: Dados nao encontrados em {btc_path}")
            print(f"    Coloque btcusdt_1m.csv na pasta {data_dir}/")
            sys.exit(1)

        btc_df = pd.read_csv(btc_path, parse_dates=["timestamp"])
        print(f"    BTC 1-min carregado: {btc_df.shape}")

        def _load_opt(filename, label):
            p = os.path.join(data_dir, filename)
            if os.path.exists(p):
                d = pd.read_csv(p, parse_dates=["timestamp"])
                print(f"    {label} carregado: {d.shape}")
                return d
            print(f"    {label} nao encontrado (opcional)")
            return None

        fng_df = _load_opt("fear_greed.csv", "Fear & Greed")
        funding_rate_df = _load_opt("funding_rate.csv", "Funding Rate")
        etf_volume_df = _load_opt("etf_btc_volume.csv", "ETF BTC Volume")
        vix_df = _load_opt("vix.csv", "VIX")
        dxy_df = _load_opt("dxy.csv", "DXY")

        # == 3. DOLLAR BARS ==================================================
        print("\n" + "=" * 70)
        print("  ETAPA 3: Dollar Bars (threshold do modelo treinado)")
        print("=" * 70)
        bar_builder = DollarBarBuilder(
            calibration_days=config["dollar_bar_calibration_days"],
            bars_per_day=config["dollar_bars_per_day"],
        )
        # Usar threshold do modelo treinado (NAO recalibrar)
        bar_builder.threshold = threshold
        dollar_bars = bar_builder.transform(btc_df)
        print(f"    Threshold usado: ${threshold:,.0f}")
        print(f"    Dollar Bars geradas: {len(dollar_bars)}")
        print(
            f"    Ticks/barra — mediana={dollar_bars['tick_count'].median():.0f}, "
            f"min={dollar_bars['tick_count'].min()}, max={dollar_bars['tick_count'].max()}"
        )

        # == 4. FEATURE ENGINEERING ==========================================
        print("\n" + "=" * 70)
        print("  ETAPA 4: Feature Engineering")
        print("=" * 70)
        registry = FeatureRegistry()
        registry.register_defaults()

        feat_config = {
            **config,
            "_fng_df": fng_df,
            "_funding_rate_df": funding_rate_df,
            "_etf_volume_df": etf_volume_df,
            "_vix_df": vix_df,
            "_dxy_df": dxy_df,
        }
        df_feat, all_feature_names = registry.compute_all(dollar_bars, feat_config)
        df_feat = df_feat.dropna(subset=all_feature_names).reset_index(drop=True)
        print(f"    Features calculadas: {len(all_feature_names)} colunas, {len(df_feat)} barras")

        # == 5. TRIPLE-BARRIER LABELING ======================================
        print("\n" + "=" * 70)
        print("  ETAPA 5: Triple-Barrier Labeling")
        print("=" * 70)
        labeler = TripleBarrierLabeler(config)
        df_labeled = labeler.apply_barriers(df_feat)

        # Extrair arrays
        X_all = df_labeled[all_feature_names].values
        y_all = df_labeled["label"].values
        close_all = df_labeled["close"].values.astype(np.float64)
        timestamps_all = df_labeled["timestamp"].values

        # Selecionar apenas features do modelo
        feat_indices = [all_feature_names.index(f) for f in selected_features]
        X_selected = X_all[:, feat_indices]
        print(f"    Barras rotuladas: {len(df_labeled)}")
        print(f"    Features usadas: {selected_features}")

        # == 6. PREDICAO =====================================================
        print("\n" + "=" * 70)
        print("  ETAPA 6: Predicao com modelo treinado")
        print("=" * 70)
        final_preds, meta_probs, primary_preds = meta.predict(X_selected)

        # Distribuicao de predicoes
        unique, counts = np.unique(final_preds, return_counts=True)
        pred_dist = dict(zip(unique.astype(int), counts.astype(int)))
        print(f"    Distribuicao predicoes (final): {pred_dist}")

        unique_p, counts_p = np.unique(primary_preds, return_counts=True)
        pred_dist_p = dict(zip(unique_p.astype(int), counts_p.astype(int)))
        print(f"    Distribuicao predicoes (primario): {pred_dist_p}")

        # Retornos
        actual_ret = np.diff(close_all, prepend=close_all[0]) / np.maximum(
            close_all, 1e-12
        )
        strat_ret = ModelEvaluator.compute_strategy_returns(
            final_preds, actual_ret,
            fee_maker=DEFAULT_CONFIG["fee_maker"],
            fee_taker=DEFAULT_CONFIG["fee_taker"],
            fee_mode=DEFAULT_CONFIG["fee_mode"],
        )

        # --- Sharpe 1: padrao (todas as barras, incluindo abstencoes) ---
        sr = np.mean(strat_ret) / max(np.std(strat_ret, ddof=1), 1e-12)
        psr = ModelEvaluator.probabilistic_sharpe_ratio(strat_ret)
        dsr = ModelEvaluator.deflated_sharpe_ratio(strat_ret, n_trials=15)

        # --- Sharpe 2: apenas trades ativos (excluindo abstencoes) ---
        active_mask = final_preds != 0
        active_ret = strat_ret[active_mask]
        n_active = active_mask.sum()
        if len(active_ret) > 2:
            sr_active = np.mean(active_ret) / max(np.std(active_ret, ddof=1), 1e-12)
            psr_active = ModelEvaluator.probabilistic_sharpe_ratio(active_ret)
            dsr_active = ModelEvaluator.deflated_sharpe_ratio(active_ret, n_trials=15)
        else:
            sr_active = psr_active = dsr_active = 0.0

        # --- Sharpe 3: vs US Risk-Free 4.5% a.a. (risk-free ajustado por barra) ---
        # Calcular duração total em dias do dataset
        ts_start = pd.to_datetime(timestamps_all[0])
        ts_end = pd.to_datetime(timestamps_all[-1])
        total_days = max((ts_end - ts_start).total_seconds() / 86400.0, 1.0)
        n_bars = len(strat_ret)
        rf_annual = 0.045  # US Fed Funds Rate (~4.5% a.a.)
        # Risk-free por barra: (1+US Risk-Free)^(dias_por_barra/365) - 1
        days_per_bar = total_days / max(n_bars, 1)
        rf_per_bar = (1.0 + rf_annual) ** (days_per_bar / 365.0) - 1.0
        # Excess returns sobre US Risk-Free
        excess_ret = strat_ret - rf_per_bar
        sr_vs_selic = np.mean(excess_ret) / max(np.std(excess_ret, ddof=1), 1e-12)
        psr_vs_selic = ModelEvaluator.probabilistic_sharpe_ratio(excess_ret)
        # Excess returns ativos sobre US Risk-Free
        active_excess = active_ret - rf_per_bar
        if len(active_excess) > 2:
            sr_active_vs_selic = np.mean(active_excess) / max(np.std(active_excess, ddof=1), 1e-12)
            psr_active_vs_selic = ModelEvaluator.probabilistic_sharpe_ratio(active_excess)
        else:
            sr_active_vs_selic = psr_active_vs_selic = 0.0

        # Rentabilidade composta
        equity_final = np.cumprod(1.0 + strat_ret)[-1]
        ret_total = (equity_final - 1.0) * 100
        btc_ret = (close_all[-1] / close_all[0] - 1.0) * 100
        selic_period_ret = ((1.0 + rf_annual) ** (total_days / 365.0) - 1.0) * 100

        # Metricas de classificacao
        meta_acc = accuracy_score(y_all, final_preds)
        meta_f1 = f1_score(y_all, final_preds, average="weighted", zero_division=0)
        cls_report = classification_report(y_all, final_preds, zero_division=0)

        print(f"    Accuracy: {meta_acc:.4f}")
        print(f"    F1 (weighted): {meta_f1:.4f}")
        print(f"\n    --- Sharpe (todas as barras, com abstencoes como 0) ---")
        print(f"    SR: {sr:.4f}  |  PSR: {psr:.4f}  |  DSR: {dsr:.4f}")
        print(f"\n    --- Sharpe (apenas {n_active} trades ativos) ---")
        print(f"    SR: {sr_active:.4f}  |  PSR: {psr_active:.4f}  |  DSR: {dsr_active:.4f}")
        print(f"\n    --- Sharpe vs US Risk-Free 4.5% a.a. (rf/barra={rf_per_bar*100:.6f}%) ---")
        print(f"    SR (all):    {sr_vs_selic:.4f}  |  PSR: {psr_vs_selic:.4f}")
        print(f"    SR (active): {sr_active_vs_selic:.4f}  |  PSR: {psr_active_vs_selic:.4f}")
        print(f"\n    --- Rentabilidade ({total_days:.1f} dias) ---")
        print(f"    Estrategia: {ret_total:+.2f}%")
        print(f"    BTC B&H:    {btc_ret:+.2f}%")
        print(f"    US Risk-Free:      {selic_period_ret:+.2f}%")
        print(f"\n{cls_report}")

        # == 7. VISUALIZACOES ================================================
        print("\n" + "=" * 70)
        print("  ETAPA 7: Gerando visualizacoes")
        print("=" * 70)

        viz.plot_regime_classification(
            timestamps_all, close_all, final_preds, primary_preds,
        )
        viz.plot_triple_barrier_labels(timestamps_all, close_all, y_all)
        viz.plot_portfolio_equity_extended(
            strat_ret, close_all, timestamps_all,
            sr, psr, dsr,
            sr_active, psr_active, dsr_active,
            sr_vs_selic, psr_vs_selic,
            sr_active_vs_selic, psr_active_vs_selic,
            rf_annual, total_days, n_active,
        )
        viz.plot_cumulative_returns(strat_ret, actual_ret, psr, dsr)
        viz.plot_meta_label_filtering(
            timestamps_all, close_all, primary_preds, final_preds,
        )
        viz.plot_confusion_matrix(y_all, final_preds)

        # == 8. RELATORIOS TXT ===============================================
        print("\n" + "=" * 70)
        print("  ETAPA 8: Salvando relatorios")
        print("=" * 70)

        # Config
        config_txt = "CONFIGURACAO DO MODELO TREINADO\n" + "=" * 60 + "\n\n"
        for k, v in config.items():
            if not k.startswith("_"):
                config_txt += f"  {k}: {v}\n"
        config_txt += f"\n  Threshold: ${threshold:,.0f}\n"
        config_txt += f"  Features selecionadas: {selected_features}\n"
        self._save_txt("config.txt", config_txt)

        # Application summary
        summary = "APPLICATION SUMMARY\n" + "=" * 60 + "\n\n"
        summary += f"  Dados: {btc_path}\n"
        summary += f"  Periodo: {btc_df['timestamp'].min()} a {btc_df['timestamp'].max()}\n"
        summary += f"  Linhas 1-min: {len(btc_df)}\n"
        summary += f"  Dollar Bars: {len(dollar_bars)}\n"
        summary += f"  Barras rotuladas: {len(df_labeled)}\n"
        summary += f"\n  Distribuicao labels (ground truth):\n"
        label_dist = dict(zip(*np.unique(y_all, return_counts=True)))
        for k, v in sorted(label_dist.items()):
            summary += f"    {int(k)}: {int(v)}\n"
        summary += f"\n  Distribuicao predicoes (final):\n"
        for k, v in sorted(pred_dist.items()):
            summary += f"    {k}: {v}\n"
        summary += f"\n  Metricas de classificacao:\n"
        summary += f"    Accuracy: {meta_acc:.4f}\n"
        summary += f"    F1 (weighted): {meta_f1:.4f}\n"
        summary += f"\n  Sharpe (todas barras, c/ abstencoes = 0):\n"
        summary += f"    SR: {sr:.4f}  |  PSR: {psr:.4f}  |  DSR: {dsr:.4f}\n"
        summary += f"\n  Sharpe (apenas {n_active} trades ativos):\n"
        summary += f"    SR: {sr_active:.4f}  |  PSR: {psr_active:.4f}  |  DSR: {dsr_active:.4f}\n"
        summary += f"\n  Sharpe vs US Risk-Free {rf_annual*100:.0f}% a.a. (rf/barra={rf_per_bar*100:.6f}%):\n"
        summary += f"    SR (all):    {sr_vs_selic:.4f}  |  PSR: {psr_vs_selic:.4f}\n"
        summary += f"    SR (active): {sr_active_vs_selic:.4f}  |  PSR: {psr_active_vs_selic:.4f}\n"
        summary += f"\n  Rentabilidade composta ({total_days:.1f} dias):\n"
        summary += f"    Estrategia: {ret_total:+.2f}%\n"
        summary += f"    BTC B&H:    {btc_ret:+.2f}%\n"
        summary += f"    US Risk-Free:      {selic_period_ret:+.2f}%\n"
        self._save_txt("application_summary.txt", summary)

        # Classification report
        self._save_txt("classification_report.txt", cls_report)

        # PSR/DSR
        psr_txt = "PSR / DSR REPORT\n" + "=" * 60 + "\n\n"
        clean_rets = strat_ret[~np.isnan(strat_ret)]
        clean_active = active_ret[~np.isnan(active_ret)] if len(active_ret) > 0 else active_ret

        psr_txt += "  1) TODAS AS BARRAS (abstencoes contam como retorno 0)\n"
        psr_txt += f"     N observacoes: {len(clean_rets)}\n"
        psr_txt += f"     Sharpe Ratio: {sr:.6f}\n"
        psr_txt += f"     PSR: {psr:.6f}\n"
        psr_txt += f"     DSR: {dsr:.6f}\n"
        psr_txt += f"     Skewness: {sp_stats.skew(clean_rets):.6f}\n"
        psr_txt += f"     Kurtosis (excess): {sp_stats.kurtosis(clean_rets):.6f}\n"

        psr_txt += f"\n  2) APENAS TRADES ATIVOS (pred != 0)\n"
        psr_txt += f"     N observacoes: {len(clean_active)}\n"
        if len(clean_active) > 2:
            psr_txt += f"     Sharpe Ratio: {sr_active:.6f}\n"
            psr_txt += f"     PSR: {psr_active:.6f}\n"
            psr_txt += f"     DSR: {dsr_active:.6f}\n"
            psr_txt += f"     Skewness: {sp_stats.skew(clean_active):.6f}\n"
            psr_txt += f"     Kurtosis (excess): {sp_stats.kurtosis(clean_active):.6f}\n"
        else:
            psr_txt += "     (insuficiente para calcular)\n"

        psr_txt += f"\n  3) SHARPE vs US Risk-Free {rf_annual*100:.0f}% a.a.\n"
        psr_txt += f"     US Risk-Free anual: {rf_annual*100:.1f}%\n"
        psr_txt += f"     Risk-free por barra: {rf_per_bar*100:.6f}%\n"
        psr_txt += f"     US Risk-Free no periodo ({total_days:.1f} dias): {selic_period_ret:+.2f}%\n"
        psr_txt += f"     SR vs US Risk-Free (all):    {sr_vs_selic:.6f}  |  PSR: {psr_vs_selic:.6f}\n"
        psr_txt += f"     SR vs US Risk-Free (active): {sr_active_vs_selic:.6f}  |  PSR: {psr_active_vs_selic:.6f}\n"

        psr_txt += f"\n  4) RENTABILIDADE COMPOSTA ({total_days:.1f} dias)\n"
        psr_txt += f"     Estrategia: {ret_total:+.2f}%\n"
        psr_txt += f"     BTC B&H:    {btc_ret:+.2f}%\n"
        psr_txt += f"     US Risk-Free:      {selic_period_ret:+.2f}%\n"
        psr_txt += f"     Excesso vs US Risk-Free: {ret_total - selic_period_ret:+.2f}%\n"
        psr_txt += f"     Excesso vs BTC:   {ret_total - btc_ret:+.2f}%\n"
        self._save_txt("psr_dsr_report.txt", psr_txt)

        # == RESULTADO FINAL =================================================
        print("\n" + "=" * 70)
        print("  APLICACAO CONCLUIDA")
        print("=" * 70)
        print(f"    Resultados salvos em: {save_dir}")
        print(f"    6 plots PNG + 4 relatorios TXT")

        return {
            "dollar_bars": len(dollar_bars),
            "labeled_bars": len(df_labeled),
            "trades_ativos": int(n_active),
            "accuracy": meta_acc,
            "f1": meta_f1,
            "sharpe_all": sr,
            "sharpe_active": sr_active,
            "sharpe_vs_selic": sr_vs_selic,
            "sharpe_active_vs_selic": sr_active_vs_selic,
            "psr": psr,
            "psr_active": psr_active,
            "dsr": dsr,
            "ret_estrategia": ret_total,
            "ret_btc": btc_ret,
            "ret_selic": selic_period_ret,
            "periodo_dias": total_days,
        }


# ===========================================================================
# MAIN
# ===========================================================================
def main() -> None:
    print("=" * 70)
    print("  APLICACAO DO MODELO — Deteccao de Regimes BTC/USDT")
    print("  Modelo treinado: save_point_advanced/trained_model.joblib")
    print("  Dados: new_data/")
    print("=" * 70)

    pipeline = ApplicationPipeline()
    results = pipeline.run()

    print("\n" + "=" * 70)
    print("  RESUMO FINAL")
    print("=" * 70)
    for k, v in results.items():
        if isinstance(v, float):
            print(f"    {k}: {v:.4f}")
        else:
            print(f"    {k}: {v}")


if __name__ == "__main__":
    main()
